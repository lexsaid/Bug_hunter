from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="qa-user",
            password="Secure-test-password-2026",
        )

    def test_login_authenticates_user_and_opens_project_list(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "qa-user",
                "password": "Secure-test-password-2026",
            },
        )

        self.assertRedirects(response, reverse("proyectos:lista_proyectos"))
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.user.pk,
        )
        self.assertEqual(
            self.client.get(reverse("proyectos:lista_proyectos")).status_code,
            200,
        )

    def test_login_returns_to_protected_page_requested_before_login(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "qa-user",
                "password": "Secure-test-password-2026",
                "next": reverse("checklist:lista"),
            },
        )

        self.assertRedirects(response, reverse("checklist:lista"))
        self.assertEqual(
            self.client.get(reverse("checklist:lista")).status_code,
            200,
        )

    def test_login_does_not_redirect_to_external_next_url(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "qa-user",
                "password": "Secure-test-password-2026",
                "next": "https://example.invalid/",
            },
        )

        self.assertRedirects(response, reverse("proyectos:lista_proyectos"))
        self.assertNotIn("next", response.url)

    def test_invalid_credentials_keep_user_unauthenticated(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "qa-user",
                "password": "incorrect-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nombre de usuario o contraseña incorrectos.")
        self.assertNotIn("_auth_user_id", self.client.session)
