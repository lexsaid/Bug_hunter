from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from checklist.models import Checklist, Criterio
from defectos.models import Defecto as SqaDefect
from matriz_trazabilidad.models import RegistroMatriz
from .models import ChecklistItem, Defect, Project, ProjectMember, TraceabilityMatrix
from .views import calculate_project_metrics


class ProjectHealthReportTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="report-user",
            password="Secure-test-password-2026",
        )
        self.project = Project.objects.create(
            name="Reporte de salud",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=self.user,
        )
        self.client.force_login(self.user)

    def add_health_report_data(self):
        checklist = Checklist.objects.create(
            nombre="Checklist reporte",
            categoria="codigo",
            project=self.project,
        )
        for state in ("cumple", "no_cumple", "no_aplica", ""):
            Criterio.objects.create(
                checklist=checklist,
                descripcion=f"Criterio {state or 'pendiente'}",
                estado=state,
            )

        complete_record = RegistroMatriz(
            id_rn="RN-01",
            id_cu="CU-01",
            nombre_cu="Caso de uso",
            id_rf="RF-01",
            id_rnf="RNF-01",
            id_modulo="MOD-01",
            id_pantalla="PANT-01",
            id_cp="CP-01",
            evidencia="https://example.com/evidence",
            project=self.project,
        )
        complete_record.save()
        RegistroMatriz.objects.create(project=self.project, id_rn="RN-02")

        defect_data = {
            "tipo_defecto": "Funcional",
            "proyecto_afectado": self.project.name,
            "tecnica_sqa": "Pruebas",
            "project": self.project,
        }
        SqaDefect.objects.create(
            descripcion="Defecto resuelto",
            severidad="Menor",
            estado="Resuelto",
            **defect_data,
        )
        SqaDefect.objects.create(
            descripcion="Defecto abierto",
            severidad="Menor",
            estado="Abierto",
            **defect_data,
        )

    def test_metrics_use_passed_over_evaluated_and_average_all_three_percentages(self):
        self.add_health_report_data()

        metrics = calculate_project_metrics(self.project)

        self.assertEqual(metrics["evaluated_checklist"], 2)
        self.assertEqual(metrics["completed_checklist"], 1)
        self.assertEqual(metrics["failed_checklist"], 1)
        self.assertEqual(metrics["checklist_percentage"], 50)
        self.assertEqual(metrics["traceability_percentage"], 50)
        self.assertEqual(metrics["defects_percentage"], 50)
        self.assertEqual(metrics["health_average"], 50)
        self.assertEqual(metrics["checklist_status"], "Malo")
        self.assertEqual(metrics["final_compliance"], "No cumple")

    def test_all_applicable_checklist_criteria_passing_is_100_percent_and_good(self):
        checklist = Checklist.objects.create(
            nombre="Checklist completo",
            categoria="codigo",
            project=self.project,
        )
        Criterio.objects.create(
            checklist=checklist,
            descripcion="Cumple",
            estado="cumple",
        )
        Criterio.objects.create(
            checklist=checklist,
            descripcion="No aplica",
            estado="no_aplica",
        )
        Criterio.objects.create(
            checklist=checklist,
            descripcion="Pendiente",
            estado="",
        )

        metrics = calculate_project_metrics(self.project)

        self.assertEqual(metrics["checklist_percentage"], 100)
        self.assertEqual(metrics["checklist_status"], "Bueno")
        self.assertEqual(metrics["defects_percentage"], 100)

    def test_html_report_shows_component_percentages_and_average(self):
        self.add_health_report_data()

        response = self.client.get(
            reverse(
                "proyectos:health_report",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "defectos resueltos")
        self.assertContains(response, "Promedio de salud del proyecto")
        self.assertContains(response, "50.0%")

    @patch("proyectos.views.canvas.Canvas")
    def test_pdf_uses_the_same_component_percentages_and_average(self, canvas_class):
        self.add_health_report_data()

        response = self.client.get(
            reverse(
                "proyectos:export_health_report_pdf",
                kwargs={"project_id": self.project.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        drawn_text = [
            call.args[2]
            for call in canvas_class.return_value.drawString.call_args_list
        ]
        self.assertTrue(any("Matriz: 50.0%" in text for text in drawn_text))
        self.assertTrue(any("Checklist: 50.0%" in text for text in drawn_text))
        self.assertTrue(any("Defectos resueltos: 50.0%" in text for text in drawn_text))
        self.assertIn("Promedio de salud: 50.0%", drawn_text)


class ProjectModelTests(TestCase):
    def test_project_sqa_records_use_the_existing_custom_user(self):
        user_model = get_user_model()
        qa_user = user_model.objects.create_user(
            username="qa-owner",
            password="Secure-test-password-2026",
        )
        developer = user_model.objects.create_user(
            username="developer",
            password="Secure-test-password-2026",
        )
        project = Project.objects.create(
            name="Bug Hunter MVP",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=qa_user,
        )

        checklist_item = ChecklistItem.objects.create(
            project=project,
            item_text="Revisar documentación",
            registered_by=developer,
        )
        defect = Defect.objects.create(
            project=project,
            description="El formulario no valida el periodo",
            reported_by=developer,
        )
        traceability_item = TraceabilityMatrix.objects.create(
            project=project,
            requirement="RN-01",
            last_modified_by=developer,
        )

        self.assertEqual(project.created_by, qa_user)
        self.assertEqual(project.checklist_items.get(), checklist_item)
        self.assertEqual(project.defects.get(), defect)
        self.assertEqual(project.traceability_items.get(), traceability_item)

    def test_new_users_can_be_created_without_a_global_project_role(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="new-developer",
            password="Secure-test-password-2026",
        )

        self.assertNotIn(
            "role",
            [field.name for field in user._meta.get_fields()],
        )


class ProjectFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.qa = user_model.objects.create_user(
            username="qa-flow",
            password="Secure-test-password-2026",
        )
        self.developer = user_model.objects.create_user(
            username="developer-flow",
            password="Secure-test-password-2026",
        )
        self.project = Project.objects.create(
            name="Proyecto compartido",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=self.qa,
        )

    def test_any_user_can_create_a_project_and_become_its_qa(self):
        self.client.force_login(self.qa)

        response = self.client.post(
            reverse("proyectos:crear_proyecto"),
            {
                "name": "Proyecto nuevo",
                "start_date": "2026-10-01",
                "end_date": "2026-11-19",
            },
        )

        project = Project.objects.get(name="Proyecto nuevo")
        self.assertRedirects(
            response,
            reverse(
                "proyectos:detalle_proyecto",
                kwargs={"project_id": project.pk},
            ),
        )
        dashboard = self.client.get(response.url)
        self.assertContains(dashboard, "Proyecto nuevo")
        self.assertContains(dashboard, "Tu rol: <strong>Técnico QA</strong>")
        self.assertContains(
            dashboard,
            reverse(
                "checklist:proyecto_lista",
                kwargs={"project_id": project.pk},
            ),
        )
        self.assertContains(
            dashboard,
            reverse(
                "defectos:proyecto_lista",
                kwargs={"project_id": project.pk},
            ),
        )

    def test_project_owner_can_invite_any_existing_user_as_developer(self):
        self.client.force_login(self.qa)

        dashboard_url = reverse(
            "proyectos:detalle_proyecto",
            kwargs={"project_id": self.project.pk},
        )
        dashboard = self.client.get(dashboard_url)
        self.assertContains(dashboard, "Agregar gente al proyecto")
        link_order = [
            "Matriz Trazabilidad",
            "Checklist",
            "Bitacora de defectos",
            "Generar reporte de salud",
        ]
        link_positions = [dashboard.content.index(label.encode()) for label in link_order]
        self.assertEqual(link_positions, sorted(link_positions))

        response = self.client.post(
            dashboard_url,
            {"user": self.developer.pk},
        )

        self.assertRedirects(
            response,
            reverse(
                "proyectos:detalle_proyecto",
                kwargs={"project_id": self.project.pk},
            ),
        )
        membership = ProjectMember.objects.get(
            project=self.project,
            user=self.developer,
        )
        self.assertEqual(membership.invited_by, self.qa)
        self.assertContains(self.client.get(response.url), "Desarrollador")

    def test_member_sees_only_projects_they_are_invited_to(self):
        other_project = Project.objects.create(
            name="Proyecto privado",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=self.qa,
        )
        ProjectMember.objects.create(
            project=self.project,
            user=self.developer,
            invited_by=self.qa,
        )
        self.client.force_login(self.developer)

        response = self.client.get(reverse("proyectos:lista_proyectos"))

        self.assertContains(response, self.project.name)
        self.assertContains(response, "Desarrollador")
        self.assertNotContains(response, other_project.name)
        self.assertContains(
            response,
            reverse(
                "proyectos:detalle_proyecto",
                kwargs={"project_id": self.project.pk},
            ),
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "proyectos:detalle_proyecto",
                    kwargs={"project_id": other_project.pk},
                )
            ).status_code,
            404,
        )

    def test_member_can_create_project_become_qa_but_cannot_invite_to_other_project(self):
        ProjectMember.objects.create(
            project=self.project,
            user=self.developer,
            invited_by=self.qa,
        )
        self.client.force_login(self.developer)

        create_response = self.client.post(
            reverse("proyectos:crear_proyecto"),
            {
                "name": "Proyecto propio del miembro",
                "start_date": "2026-10-01",
                "end_date": "2026-11-19",
            },
        )
        self.assertEqual(create_response.status_code, 302)
        created_project = Project.objects.get(name="Proyecto propio del miembro")
        self.assertEqual(created_project.created_by, self.developer)
        self.assertContains(
            self.client.get(
                reverse(
                    "proyectos:detalle_proyecto",
                    kwargs={"project_id": created_project.pk},
                )
            ),
            "Tu rol: <strong>Técnico QA</strong>",
        )
        self.assertEqual(
            self.client.post(
                reverse(
                    "proyectos:detalle_proyecto",
                    kwargs={"project_id": self.project.pk},
                ),
                {"user": self.developer.pk},
            ).status_code,
            403,
        )

    def test_django_admin_is_enabled_without_a_link_in_project_ui(self):
        response = self.client.get("/admin/")

        self.assertRedirects(
            response,
            "/admin/login/?next=/admin/",
            fetch_redirect_response=False,
        )
        self.client.force_login(self.qa)
        project_list = self.client.get(reverse("proyectos:lista_proyectos"))
        self.assertNotContains(project_list, "/admin/")

        admin_user = get_user_model().objects.create_superuser(
            username="admin-user",
            password="admin-test-password-2026",
        )
        self.client.force_login(admin_user)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
