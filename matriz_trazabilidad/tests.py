from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from proyectos.models import Project, ProjectMember
from proyectos.views import calculate_project_metrics
from .models import RegistroMatriz


class ProjectTraceabilityFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="matrix-owner",
            password="Secure-test-password-2026",
        )
        self.member = user_model.objects.create_user(
            username="matrix-member",
            password="Secure-test-password-2026",
        )
        self.project = Project.objects.create(
            name="Proyecto matriz",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=self.owner,
        )
        ProjectMember.objects.create(
            project=self.project,
            user=self.member,
            invited_by=self.owner,
        )
        self.client.force_login(self.member)

    def test_project_dashboard_links_to_scoped_traceability_matrix(self):
        dashboard_url = reverse(
            "proyectos:detalle_proyecto",
            kwargs={"project_id": self.project.pk},
        )
        response = self.client.get(dashboard_url)

        matrix_url = reverse(
            "matriz_trazabilidad:proyecto_lista",
            kwargs={"project_id": self.project.pk},
        )
        self.assertContains(response, matrix_url)
        self.assertEqual(self.client.get(matrix_url).status_code, 200)

    def test_new_requirement_is_linked_and_visible_only_in_its_project(self):
        response = self.client.post(
            reverse(
                "matriz_trazabilidad:proyecto_registrar_rn",
                kwargs={"project_id": self.project.pk},
            ),
            {"id_rn": "RN-01"},
        )

        record = RegistroMatriz.objects.get()
        self.assertEqual(record.project, self.project)
        self.assertRedirects(
            response,
            reverse(
                "matriz_trazabilidad:proyecto_lista",
                kwargs={"project_id": self.project.pk},
            ),
        )
        project_matrix = self.client.get(
            reverse(
                "matriz_trazabilidad:proyecto_lista",
                kwargs={"project_id": self.project.pk},
            )
        )
        global_matrix = self.client.get(
            reverse("matriz_trazabilidad:vista_matriz")
        )
        self.assertContains(project_matrix, "RN-01")
        self.assertNotContains(global_matrix, "RN-01")
        add_cu_url = reverse(
            "matriz_trazabilidad:proyecto_registrar_cu",
            kwargs={"project_id": self.project.pk, "pk": record.pk},
        )
        self.assertContains(project_matrix, add_cu_url)

        self.client.post(
            add_cu_url,
            {"id_cu": "CU-01", "nombre_cu": "Crear proyecto"},
        )
        child_record = RegistroMatriz.objects.get(
            project=self.project,
            id_cu="CU-01",
        )
        self.assertEqual(child_record.id_rn, "RN-01")

    def test_requirement_identifiers_can_repeat_across_projects_not_within_one(self):
        other_project = Project.objects.create(
            name="Otro proyecto",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=self.owner,
        )
        RegistroMatriz.objects.create(project=self.project, id_rn="RN-01")
        self.client.force_login(self.owner)

        duplicate_response = self.client.post(
            reverse(
                "matriz_trazabilidad:proyecto_registrar_rn",
                kwargs={"project_id": self.project.pk},
            ),
            {"id_rn": "RN-01"},
        )
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(
            RegistroMatriz.objects.filter(project=self.project).count(),
            1,
        )

        other_response = self.client.post(
            reverse(
                "matriz_trazabilidad:proyecto_registrar_rn",
                kwargs={"project_id": other_project.pk},
            ),
            {"id_rn": "RN-01"},
        )
        self.assertEqual(other_response.status_code, 302)
        self.assertTrue(
            RegistroMatriz.objects.filter(
                project=other_project,
                id_rn="RN-01",
            ).exists()
        )

    def test_project_route_cannot_access_another_projects_record(self):
        other_project = Project.objects.create(
            name="Proyecto privado",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=self.owner,
        )
        record = RegistroMatriz.objects.create(
            project=other_project,
            id_rn="RN-PRIVATE",
        )

        response = self.client.get(
            reverse(
                "matriz_trazabilidad:proyecto_registrar_cu",
                kwargs={"project_id": self.project.pk, "pk": record.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_project_health_report_counts_complete_matrix_records(self):
        complete = RegistroMatriz(
            id_rn="RN-01",
            id_cu="CU-01",
            nombre_cu="Crear proyecto",
            id_rf="RF-01",
            id_rnf="RNF-01",
            id_modulo="MOD-01",
            id_pantalla="PANT-01",
            id_cp="CP-01",
            evidencia="https://example.com/evidence",
            project=self.project,
        )
        complete.save()
        RegistroMatriz.objects.create(project=self.project, id_rn="RN-02")

        metrics = calculate_project_metrics(self.project)

        self.assertEqual(metrics["total_traceability"], 2)
        self.assertEqual(metrics["traceability_percentage"], 50)
