from datetime import date

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Checklist, Criterio
from proyectos.models import Project, ProjectMember


class ChecklistFlowTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username="qa-user",
            password="Secure-test-password-2026",
        )
        self.client.force_login(usuario)

    def test_main_page_shows_create_button_and_empty_state_without_counter(self):
        response = self.client.get(reverse("checklist:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crear nuevo checklist")
        self.assertContains(response, "Todavía no hay checklists")
        self.assertNotContains(response, "0 criterios")

    def test_create_page_requires_custom_type_for_other(self):
        create_url = reverse("checklist:crear")
        response = self.client.post(
            create_url,
            {
                "nombre": "Lista personalizada",
                "categoria": "otros",
                "tipo_personalizado": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Checklist.objects.exists())

        response = self.client.post(
            create_url,
            {
                "nombre": "Lista personalizada",
                "categoria": "otros",
                "tipo_personalizado": "Accesibilidad",
            },
        )
        checklist = Checklist.objects.get()
        self.assertRedirects(
            response,
            reverse("checklist:detalle", kwargs={"pk": checklist.pk}),
        )
        self.assertEqual(checklist.tipo_display, "Accesibilidad")

    def test_create_checklist_redirects_to_its_criteria_table(self):
        response = self.client.post(
            reverse("checklist:crear"),
            {"nombre": "Revisión de documentos", "categoria": "documento"},
        )

        checklist = Checklist.objects.get()
        self.assertRedirects(
            response,
            reverse("checklist:detalle", kwargs={"pk": checklist.pk}),
        )
        self.assertContains(self.client.get(response.url), "Número de la fila")
        self.assertContains(self.client.get(response.url), "Guardar")

    def test_detail_page_adds_and_updates_criteria(self):
        checklist = Checklist.objects.create(nombre="Código", categoria="codigo")
        url = reverse("checklist:detalle", kwargs={"pk": checklist.pk})
        estados = dict(Criterio.ESTADOS)

        self.assertEqual(len(estados), 3)
        self.assertContains(self.client.get(url), "No aplica")

        response = self.client.post(
            url,
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-descripcion": "Validar los nombres de variables",
                "form-0-estado": "cumple",
                "form-0-observaciones": "Revisado en equipo",
            },
        )
        criterio = Criterio.objects.get(checklist=checklist)
        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(criterio.estado, "cumple")

        response = self.client.post(
            url,
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-descripcion": criterio.descripcion,
                "form-0-estado": "no_aplica",
                "form-0-observaciones": "No aplica a este módulo",
            },
        )
        criterio.refresh_from_db()
        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(criterio.estado, "no_aplica")
        self.assertEqual(criterio.observaciones, "No aplica a este módulo")

    def test_detail_page_saves_multiple_table_rows_together(self):
        checklist = Checklist.objects.create(nombre="Checklist", categoria="documento")

        response = self.client.post(
            reverse("checklist:detalle", kwargs={"pk": checklist.pk}),
            {
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-descripcion": "Revisar ortografía",
                "form-0-estado": "cumple",
                "form-0-observaciones": "",
                "form-1-descripcion": "Confirmar referencias",
                "form-1-estado": "no_cumple",
                "form-1-observaciones": "Falta una referencia",
            },
        )

        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(checklist.criterios.count(), 2)

    def test_submitted_criteria_are_saved_under_the_active_checklist(self):
        checklist = Checklist.objects.create(nombre="A", categoria="otros")
        otro_checklist = Checklist.objects.create(nombre="B", categoria="otros")
        criterio = Criterio.objects.create(
            checklist=checklist,
            descripcion="Criterio existente",
        )

        response = self.client.post(
            reverse("checklist:detalle", kwargs={"pk": otro_checklist.pk}),
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-descripcion": "Nuevo criterio para B",
                "form-0-estado": "cumple",
                "form-0-observaciones": "",
            },
        )
        self.assertRedirects(response, reverse("checklist:lista"))
        criterio.refresh_from_db()
        self.assertEqual(criterio.descripcion, "Criterio existente")
        nuevo_criterio = Criterio.objects.get(
            checklist=otro_checklist,
            descripcion="Nuevo criterio para B",
        )
        self.assertEqual(nuevo_criterio.estado, "cumple")

    def test_list_shows_separate_edit_and_evaluation_actions(self):
        checklist = Checklist.objects.create(nombre="Documentos", categoria="documento")

        response = self.client.get(reverse("checklist:lista"))

        self.assertContains(
            response,
            reverse("checklist:editar", kwargs={"pk": checklist.pk}),
        )
        self.assertContains(
            response,
            reverse("checklist:evaluar", kwargs={"pk": checklist.pk}),
        )
        self.assertContains(response, "Editar")
        self.assertContains(response, "Iniciar checklist")

    def test_edit_checklist_updates_metadata_structure_and_status(self):
        checklist = Checklist.objects.create(
            nombre="Revisión inicial",
            categoria="documento",
        )
        criterio = Criterio.objects.create(
            checklist=checklist,
            descripcion="Validar enlaces",
            estado="no_cumple",
            observaciones="Pendiente de evaluación",
        )

        edit_url = reverse("checklist:editar", kwargs={"pk": checklist.pk})
        edit_page = self.client.get(edit_url)
        self.assertContains(edit_page, "CU-09")
        self.assertContains(edit_page, 'name="form-0-estado"')
        self.assertContains(edit_page, "No aplica")

        response = self.client.post(
            edit_url,
            {
                "nombre": "Revisión documental",
                "categoria": "documento",
                "tipo_personalizado": "",
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": str(criterio.pk),
                "form-0-descripcion": "Validar referencias",
                "form-0-estado": "cumple",
                "form-0-observaciones": "Revisar enlaces internos",
                "form-1-id": "",
                "form-1-descripcion": "Comprobar enlaces externos",
                "form-1-estado": "no_aplica",
                "form-1-observaciones": "No hay enlaces externos",
            },
        )

        checklist.refresh_from_db()
        criterio.refresh_from_db()
        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(checklist.nombre, "Revisión documental")
        self.assertEqual(criterio.descripcion, "Validar referencias")
        self.assertEqual(criterio.observaciones, "Revisar enlaces internos")
        self.assertEqual(criterio.estado, "cumple")
        criterio_nuevo = Checklist.objects.get(pk=checklist.pk).criterios.get(
            descripcion="Comprobar enlaces externos"
        )
        self.assertEqual(criterio_nuevo.checklist, checklist)
        self.assertEqual(criterio_nuevo.estado, "no_aplica")
        self.assertContains(self.client.get(edit_url), "Cumplimiento")
        self.assertContains(self.client.get(edit_url), "No aplica")

    def test_edit_checklist_can_remove_a_criterion(self):
        checklist = Checklist.objects.create(nombre="Otros", categoria="otros")
        criterio = Criterio.objects.create(
            checklist=checklist,
            descripcion="Criterio a eliminar",
        )

        response = self.client.post(
            reverse("checklist:editar", kwargs={"pk": checklist.pk}),
            {
                "nombre": "Otros",
                "categoria": "otros",
                "tipo_personalizado": "General",
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": str(criterio.pk),
                "form-0-descripcion": criterio.descripcion,
                "form-0-estado": "",
                "form-0-observaciones": "",
                "form-0-DELETE": "on",
                "form-1-id": "",
                "form-1-descripcion": "",
                "form-1-estado": "",
                "form-1-observaciones": "",
            },
        )

        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertFalse(Criterio.objects.filter(pk=criterio.pk).exists())

    def test_editing_other_type_shows_custom_type_input(self):
        checklist = Checklist.objects.create(
            nombre="Lista personalizada",
            categoria="otros",
            tipo_personalizado="Accesibilidad",
        )

        response = self.client.get(
            reverse("checklist:editar", kwargs={"pk": checklist.pk})
        )

        self.assertContains(
            response,
            'id="custom-type-container" class="custom-type-container"',
        )
        self.assertContains(response, 'value="Accesibilidad"')

    def test_missing_custom_type_keeps_the_input_visible_with_validation_error(self):
        checklist = Checklist.objects.create(
            nombre="Lista personalizada",
            categoria="otros",
            tipo_personalizado="Accesibilidad",
        )

        response = self.client.post(
            reverse("checklist:editar", kwargs={"pk": checklist.pk}),
            {
                "nombre": "Lista personalizada",
                "categoria": "otros",
                "tipo_personalizado": "",
                "form-TOTAL_FORMS": "0",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'id="custom-type-container" class="custom-type-container"',
        )
        self.assertContains(response, "Escribe el tipo de checklist.")

    def test_changing_other_to_standard_category_clears_custom_type(self):
        checklist = Checklist.objects.create(
            nombre="Lista personalizada",
            categoria="otros",
            tipo_personalizado="Accesibilidad",
        )

        response = self.client.post(
            reverse("checklist:editar", kwargs={"pk": checklist.pk}),
            {
                "nombre": "Lista personalizada",
                "categoria": "codigo",
                "tipo_personalizado": "Accesibilidad",
                "form-TOTAL_FORMS": "0",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
            },
        )

        checklist.refresh_from_db()
        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(checklist.categoria, "codigo")
        self.assertEqual(checklist.tipo_personalizado, "")

    def test_evaluation_updates_only_status_and_observations(self):
        checklist = Checklist.objects.create(nombre="Código", categoria="codigo")
        criterio = Criterio.objects.create(
            checklist=checklist,
            descripcion="Revisar nombres",
            observaciones="Nota original",
        )
        url = reverse("checklist:evaluar", kwargs={"pk": checklist.pk})

        self.assertContains(self.client.get(url), "CU-10")
        response = self.client.post(
            url,
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": str(criterio.pk),
                "form-0-estado": "cumple",
                "form-0-observaciones": "Evaluado correctamente",
                "form-0-descripcion": "Texto que no debe guardarse desde evaluación",
            },
        )

        criterio.refresh_from_db()
        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(criterio.estado, "cumple")
        self.assertEqual(criterio.observaciones, "Evaluado correctamente")
        self.assertEqual(criterio.descripcion, "Revisar nombres")

    def test_project_checklists_are_linked_and_isolated_from_global_list(self):
        project = Project.objects.create(
            name="Proyecto checklist",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=get_user_model().objects.get(username="qa-user"),
        )

        response = self.client.post(
            reverse(
                "checklist:proyecto_crear",
                kwargs={"project_id": project.pk},
            ),
            {"nombre": "Checklist del proyecto", "categoria": "codigo"},
        )
        checklist = Checklist.objects.get(nombre="Checklist del proyecto")

        self.assertEqual(checklist.project, project)
        self.assertRedirects(
            response,
            reverse(
                "checklist:proyecto_detalle",
                kwargs={"project_id": project.pk, "pk": checklist.pk},
            ),
        )
        project_response = self.client.get(
            reverse(
                "checklist:proyecto_lista",
                kwargs={"project_id": project.pk},
            )
        )
        global_response = self.client.get(reverse("checklist:lista"))
        self.assertContains(project_response, checklist.nombre)
        self.assertNotContains(global_response, checklist.nombre)

    def test_project_developer_cannot_view_or_modify_checklists(self):
        user_model = get_user_model()
        developer = user_model.objects.create_user(
            username="checklist-developer",
            password="Secure-test-password-2026",
        )
        qa = user_model.objects.get(username="qa-user")
        project = Project.objects.create(
            name="Proyecto compartido",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=qa,
        )
        ProjectMember.objects.create(
            project=project,
            user=developer,
            invited_by=qa,
        )
        checklist = Checklist.objects.create(
            nombre="Solo visible",
            categoria="codigo",
            project=project,
        )
        self.client.force_login(developer)

        list_url = reverse(
            "checklist:proyecto_lista",
            kwargs={"project_id": project.pk},
        )
        self.assertEqual(self.client.get(list_url).status_code, 403)
        self.assertEqual(
            self.client.get(
                reverse(
                    "checklist:proyecto_detalle",
                    kwargs={"project_id": project.pk, "pk": checklist.pk},
                )
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "checklist:proyecto_editar",
                    kwargs={"project_id": project.pk, "pk": checklist.pk},
                )
            ).status_code,
            403,
        )

        dashboard = self.client.get(
            reverse(
                "proyectos:detalle_proyecto",
                kwargs={"project_id": project.pk},
            )
        )
        self.assertNotContains(dashboard, list_url)

    def test_project_owner_can_view_checklist_from_project_dashboard(self):
        project = Project.objects.create(
            name="Proyecto QA",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 11, 19),
            created_by=get_user_model().objects.get(username="qa-user"),
        )

        dashboard = self.client.get(
            reverse(
                "proyectos:detalle_proyecto",
                kwargs={"project_id": project.pk},
            )
        )
        checklist_url = reverse(
            "checklist:proyecto_lista",
            kwargs={"project_id": project.pk},
        )

        self.assertContains(dashboard, checklist_url)
        self.assertEqual(self.client.get(checklist_url).status_code, 200)
