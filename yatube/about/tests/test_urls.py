from django.test import Client, TestCase
from django.contrib.auth import get_user_model

from http import HTTPStatus

User = get_user_model()


class PagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="vasya")

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.templates_url_names = (
            "/about/author/",
            "/about/tech/",
        )

    def test_guest_url_exists_at_desired_location(self):
        """URL-адрес доступен гостю."""
        for url in self.templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_url_exists_at_desired_location(self):
        """URL-адрес доступен авторизованному пользователю."""
        for url in self.templates_url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "about/author.html": "/about/author/",
            "about/tech.html": "/about/tech/",
        }

        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
