from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="vasya")
        cls.group = Group.objects.create(
            title="Test Title",
            slug="test-group",
            description="Description",
        )
        cls.post = Post.objects.create(
            text="Test text",
            author=PagesURLTests.user,
            group=PagesURLTests.group,
        )

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user = User.objects.create_user(username="pupkin")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.templates_url_names = (
            "/",
            "/about/author/",
            "/about/tech/",
            "/group/test-group/",
            "/vasya/",
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
            "posts/index.html": "/",
            "posts/newpost.html": "/new/",
            "posts/group.html": "/group/test-group/",
            "posts/profile.html": "/vasya/",
            "posts/post.html": reverse(
                "post", kwargs={
                    "username": "vasya",
                    "post_id": PagesURLTests.post.id}
            ),
        }

        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_newpost_url_redirect_anonymous_on_admin_login(self):
        """Страница /new/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get("/new/", follow=True)

        self.assertRedirects(response, "/auth/login/?next=/new/")

    def test_non_url_redirect_on_404_500(self):
        """Возвращает ли сервер код 404, если страница не найдена."""
        self.templates_non_url = (
            "/misc/404/",
            "/misc/500/",
        )

        for url in self.templates_non_url:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
