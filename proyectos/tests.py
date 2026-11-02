from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ChecklistItem, Defect, Project, ProjectMember, TraceabilityMatrix


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

        response = self.client.post(
            reverse(
                "proyectos:detalle_proyecto",
                kwargs={"project_id": self.project.pk},
            ),
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
