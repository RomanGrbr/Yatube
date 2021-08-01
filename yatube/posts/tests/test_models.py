from django.test import TestCase

from ..models import Post, Group, User


class ModelPostTest(TestCase):
    """Тестируем класс Post"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username="pupkin")
        cls.post = Post.objects.create(text="1234567890123456789", author=user)

    def test_str_post(self):
        """Тестируем метод __str__"""
        post_str = ModelPostTest.post

        expected_text = str(post_str)

        self.assertEqual(
            expected_text, "123456789012345", "Метод __str__ работает "
                                              "неправильно "
        )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        task = ModelPostTest.post

        field_help_texts = {
            "text": "Напишите что нибудь интересное",
            "group": "Выбирете группу публикации",
        }

        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    task._meta.get_field(value).help_text, expected
                )


class ModelGroupTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Супер", description="Проводим уроки тестирования"
        )

    def test_str_group(self):
        """Тестируем метод __str__"""
        group_str = ModelGroupTest.group

        expected_text = str(group_str)

        self.assertEqual(expected_text, "Супер",
                         "Метод __str__ работает неправильно"
                         )
