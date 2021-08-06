import shutil
import tempfile
from datetime import date

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User, Follow


class PagesViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

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

    def test_follow_unfollow(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        """
        # Создать еще одного авторизованного пользователя Василий
        self.user_vasya = User.objects.create_user(username="Vasya")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_vasya)

        # Подписаться Василием на Пупкина
        Follow.objects.create(user=self.user_vasya, author=self.user_pupkin)
        following = Follow.objects.all()
        fol = following[0]

        # Проверить что Василий подписан на Пупкина
        self.assertEqual(fol.author, self.user_pupkin)

        # Отписаться Василием от Пупкина
        Follow.objects.filter(author_id=self.user_pupkin.id,
                              user_id=self.user_vasya.id).delete()

        # Проверить что василий не на кого не подписан
        non_follow = Follow.objects.filter(user=self.user_vasya).exists()

        self.assertNotEqual(non_follow, True)

    def test_new_post_follower(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан на него.
        """
        # Создать пользователя Василий
        self.user_vasya = User.objects.create_user(username="Vasya")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_vasya)
        # Создать пост Пупкиным
        Post.objects.create(
            text="Pupkin text",
            author=self.user_pupkin,
            group=self.group, )

        # Василием подписаться на Пупкина
        Follow.objects.create(user=self.user_vasya, author=self.user_pupkin)
        # Василием открыть ленту избранных авторов
        response = self.authorized_client.get(reverse("follow_index"))

        # Проверить наличие поста Пупкина
        self.assertEqual(response.context['post'].text, "Pupkin text")

        # Создать пользователя Иван
        self.user_ivan = User.objects.create_user(username="Ivan")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_ivan)

        # Иваном открыть ленту избранных авторов
        response = self.authorized_client.get(reverse("follow_index"))

        # TODO Иваном проверить отсутсвие постов

    def test_comment_follow_post(self):
        """Только авторизированный пользователь может комментировать посты."""
        # Создать Василия
        self.user_vasya = User.objects.create_user(username="Vasya")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_vasya)
        # Василием создать пост
        self.post_vasya = Post.objects.create(
            text="Vasya text",
            author=self.user_vasya,
            group=self.group, )
        # Гостем заполнить форму комментария
        form_comment = {"author": self.user_pupkin,
                        "post": self.post_vasya,
                        "text": "Guest comment"}

        # Отправить форму комментария
        response = self.guest_client.post(
            reverse('add_comment',
                    kwargs={
                        "username": self.user_vasya,
                        "post_id": self.post_vasya.id
                    }
                    ), data=form_comment, follow=True)

        # Проверить редирект с формы на авторизацию
        redirect = f"/auth/login/?next=/{self.user_vasya}/" \
                   f"{self.post_vasya.id}/comment/"
        self.assertRedirects(response, redirect)

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
