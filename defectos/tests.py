from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from proyectos.models import Project, ProjectMember
from .models import Defecto


class ProjectDefectFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.qa = user_model.objects.create_user(
            username="defect-qa",
            password="Secure-test-password-2026",
        )
        self.developer = user_model.objects.create_user(
            username="defect-developer",
            password="Secure-test-password-2026",
        )
        self.project = Project.objects.create(
            name="Proyecto de defectos",
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

    def test_defect_created_from_project_is_associated_and_shown_in_scope(self):
        response = self.client.post(
            reverse(
                "defectos:proyecto_crear",
                kwargs={"project_id": self.project.pk},
            ),
            {
                "descripcion": "El botón no responde",
                "tipo_defecto": "Interfaz",
                "tecnica_sqa": "Prueba funcional",
                "severidad": "Menor",
            },
        )

        defect = Defecto.objects.get()
        self.assertEqual(defect.project, self.project)
        self.assertEqual(defect.proyecto_afectado, self.project.name)
        self.assertRedirects(
            response,
            reverse(
                "defectos:proyecto_lista",
                kwargs={"project_id": self.project.pk},
            ),
        )
        self.assertContains(
            self.client.get(
                reverse(
                    "defectos:proyecto_lista",
                    kwargs={"project_id": self.project.pk},
                )
            ),
            defect.codigo,
        )
        self.assertNotContains(
            self.client.get(reverse("defectos:lista")),
            defect.codigo,
        )

    def test_project_defect_route_cannot_resolve_defect_from_another_project(self):
        other_project = Project.objects.create(
            name="Otro proyecto",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=self.qa,
        )
        defect = Defecto.objects.create(
            descripcion="Defecto ajeno",
            tipo_defecto="Interfaz",
            proyecto_afectado=other_project.name,
            tecnica_sqa="Prueba funcional",
            project=other_project,
        )

        response = self.client.get(
            reverse(
                "defectos:proyecto_resolver",
                kwargs={
                    "project_id": self.project.pk,
                    "defecto_id": defect.pk,
                },
            )
        )

        defect.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(defect.estado, "Abierto")
