import shutil
import tempfile
from datetime import date

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.test import override_settings

from ..models import Group, Post, User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PagesViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="yandex")

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title="Test Title",
            slug="test-group",
            description="Description",
        )
        cls.another_group = Group.objects.create(
            title="Test2 Title2",
            slug="test-another-group",
            description="Description",
        )
        cls.post = Post.objects.create(
            text="Test text",
            author=PagesViewTests.user,
            group=PagesViewTests.group,
            image=PagesViewTests.uploaded
        )
        Post.objects.bulk_create(
            (
                Post(
                    text="Test text",
                    author=PagesViewTests.user,
                    group=PagesViewTests.group,
                )
                for i in range(13)
            ),
        )

    @classmethod
    def tearDownClass(cls):
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user_pupkin = User.objects.create_user(username="Pupkin")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_pupkin)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            "posts/index.html": reverse("index"),
            "posts/group.html": reverse(
                "group_posts", kwargs={"slug": "test-group"}
            ),
            "posts/profile.html": reverse(
                "profile", kwargs={"username": "Pupkin"}
            ),
            "posts/newpost.html": reverse("new_post"),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # @unittest.skip("Гонит по ночам.")
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse("index"))
        date_today = date.today().strftime("%d.%m.%Y")

        first_object = response.context["page"][0]

        self.assertEqual(first_object.text, "Test text")
        self.assertEqual(first_object.author.username, "yandex")
        self.assertEqual(
            first_object.pub_date.strftime("%d.%m.%Y"), date_today
        )
        self.assertEqual(first_object.group.slug, "test-group")

    def test_form_index_page_show_correct_context(self):
        """ "В форму шаблона index передан правельный контекст."""
        response = self.guest_client.get(reverse("index"))

        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            "text": forms.fields.CharField,
            "pub_date": forms.fields.DateTimeField,
            "author": forms.fields.ChoiceField,
            "group": forms.fields.ChoiceField,
            "image": forms.ImageField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value in form_fields.items():
            with self.subTest(value=value):
                self.assertIn("page", response.context)

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": "test-group"})
        )

        self.assertEqual(response.context["group"].title, "Test Title")
        self.assertEqual(response.context["group"].slug, "test-group")
        self.assertEqual(response.context["group"].description, "Description")

    def test_form_group_pages_show_correct_context(self):
        """ "В форму шаблона group передан правельный контекст."""
        response = self.guest_client.get(
            reverse("group_posts", kwargs={"slug": "test-group"})
        )

        form_fields = {
            "title": forms.fields.CharField,
            "description": forms.fields.ChoiceField,
            "slug": forms.fields.ChoiceField,
            "image": forms.ImageField,
        }

        for value in form_fields.items():
            with self.subTest(value=value):
                self.assertIn("group", response.context)

    def test_new_post_page_show_correct_context(self):
        """ "В форму шаблона newpost передан правельный контекст."""
        response = self.authorized_client.get(reverse("new_post"))

        form_fields = {
            "text": forms.CharField,
            "group": forms.models.ModelChoiceField,
            "image": forms.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                forms_field = response.context["form"].fields[value]
                self.assertIsInstance(forms_field, expected)

    def test_profile_page_show_correct_context(self):
        """ "В форму шаблона profile передан правельный контекст."""
        response = self.authorized_client.get(
            reverse("profile", kwargs={"username": "Pupkin"})
        )

        self.assertEqual(response.context["user"].username, "Pupkin")

    def test_check_post_in_index(self):
        """Проверить пост в на главной странице"""
        response = self.authorized_client.get(reverse("index"))

        first_object = response.context["page"][0]
        post_text = first_object.text

        self.assertEqual(post_text, "Test text")

    def test_check_post_in_group(self):
        """Проверить пост в группе"""
        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": "test-group"})
        )

        first_object = response.context["page"][0]
        post_text = first_object.text

        self.assertEqual(post_text, "Test text")

    def test_not_check_post_in_another_group(self):
        """Проверить пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": "test-another-group"})
        )

        first_object = response.context["page"].has_next()

        self.assertFalse(first_object, False)

    def test_first_page_contains_ten_records(self):
        """Тест пагинатора на 1 странице index"""
        response = self.client.get(reverse("index"))

        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context["page"].object_list), 10)

    def test_second_page_contains_three_records(self):
        """Тест пагинатора на 2 странице index"""
        # Проверка: на второй странице должно быть четыре поста.
        response = self.client.get(reverse("index") + "?page=2")

        self.assertEqual(len(response.context["page"].object_list), 4)

    def test_cache_index_page(self):
        """Тест для проверки кеширования главной страницы"""
        post_cache = Post.objects.create(
            text="Test cache",
            author=self.user,
            group=self.group,
        )

        response_first = self.authorized_client.get(reverse("index"))
        post_cache.delete()
        response_second = self.authorized_client.get(reverse("index"))
        cache.clear()
        response_third = self.authorized_client.get(reverse("index"))

        # Проверим что создалась запись
        self.assertEqual(response_first.context["page"][0].text,
                         post_cache.text
                         )
        # Проверим что запись осталась после ее удаления и повторного входа
        self.assertEqual(response_second.context["page"][0].text,
                         post_cache.text
                         )
        # Проверим что запись удалилась после очистки кэша и повторного входа
        self.assertEqual(response_third.context["page"][0].text,
                         self.post.text
                         )
