import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.test import override_settings

from ..forms import PostForm
from ..models import Group, Post, User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="yandex")
        cls.group = Group.objects.create(
            title="Test Title",
            slug="test-group",
            description="Description",
        )
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.post = Post.objects.create(
            text="Test text",
            author=PostCreateFormTests.user,
            group=PostCreateFormTests.group,
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.user = User.objects.create_user(username="pupkin")
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        cache.clear()

    def test_create_post(self):
        """Создание поста с редиректом"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {"text": "Test text2",
                     "group": PostCreateFormTests.group.id,
                     "image": uploaded,
                     }

        response = self.authorized_client.post(
            reverse("new_post"), data=form_data, follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse("index"))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверяем, что создалась запись с нашим слагом
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group.id,
                text="Test text2",
                author=PostCreateFormTests.user.id,
                image='posts/small.gif',
            ).exists()
        )

        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_text_group_post(self):
        """Редактирование только текста поста"""
        form_edit = {
            "text": "Test text3",
        }

        self.authorized_client.post(
            reverse("post_edit",
                    kwargs={"username": "yandex", "post_id": self.post.id}
                    ),
            data=form_edit, follow=True
        )

        self.post.refresh_from_db()
        self.assertEqual(self.post.text, "Test text3")
        self.assertIsNone(self.post.group)

    def test_edit_post(self):
        """Редактирование и текста и группы поста"""
        group_new = Group.objects.create(
            title="Test Title",
            slug="test-group-new",
            description="Description",
        )
        form_edit = {
            "text": "Test text4",
            "group": group_new.id,
        }

        self.authorized_client.post(
            reverse("post_edit",
                    kwargs={"username": "yandex", "post_id": self.post.id}
                    ),
            data=form_edit, follow=True
        )

        self.assertTrue(
            Post.objects.filter(
                text="Test text4",
                author=PostCreateFormTests.user.id,
                group=group_new.id
            ).exists()
        )

        self.post.refresh_from_db()
        self.assertEqual(self.post.text, "Test text4")
        self.assertEqual(group_new.slug, "test-group-new")

    def test_create_post_without_group(self):
        """Создание поста без группы"""
        form_data = {"text": "Test text4"}

        response = self.authorized_client.post(
            reverse("new_post"), data=form_data, follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(
            Post.objects.filter(
                text="Test text4",
                author=PostCreateFormTests.user.id,
                group__isnull=True,
            ).exists()
        )
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, HTTPStatus.OK)
