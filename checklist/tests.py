from django.test import TestCase

from django.urls import reverse

from .models import Checklist, Criterio


class ChecklistFlowTests(TestCase):
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
                "form-1-descripcion": "",
                "form-1-estado": "",
                "form-1-observaciones": "",
            },
        )

        checklist.refresh_from_db()
        criterio.refresh_from_db()
        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(checklist.nombre, "Revisión documental")
        self.assertEqual(criterio.descripcion, "Validar referencias")
        self.assertEqual(criterio.observaciones, "Revisar enlaces internos")
        self.assertEqual(criterio.estado, "cumple")
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
