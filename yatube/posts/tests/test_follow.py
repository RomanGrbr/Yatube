from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User, Follow


class FollowViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username="Masha")

        cls.group = Group.objects.create(
            title="Test Title",
            slug="test-group",
            description="Description",
        )

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user_pupkin = User.objects.create_user(username="Pupkin")
        self.user_vasya = User.objects.create_user(username="Vasya")
        self.user_ivan = User.objects.create_user(username="Ivan")
        self.authorized_client_pupkin = Client()
        self.authorized_client_vasya = Client()
        self.authorized_client_ivan = Client()
        self.authorized_client_pupkin.force_login(self.user_pupkin)
        self.authorized_client_vasya.force_login(self.user_vasya)
        self.authorized_client_ivan.force_login(self.user_ivan)
        cache.clear()

    def test_follow(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        """
        # Подписаться Василием на Пупкина
        Follow.objects.create(user=self.user_vasya, author=self.user_pupkin)
        following = Follow.objects.all()
        fol = following[0]

        # Проверить что Василий подписан на Пупкина
        self.assertEqual(fol.author, self.user_pupkin)

    def test_unfollow(self):
        # Отписаться Василием от Пупкина
        Follow.objects.filter(author_id=self.user_pupkin.id,
                              user_id=self.user_vasya.id).delete()

        non_follow = Follow.objects.filter(user=self.user_vasya).exists()

        # Проверить что василий не на кого не подписан
        self.assertNotEqual(non_follow, True)

    def test_new_post_follower(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан на него.
        """
        # Создать пост Пупкиным
        pupkin_post = Post.objects.create(
            text="Pupkin text",
            author=self.user_pupkin,
            group=self.group,
        )
        # Создать пост Иваном
        ivan_post = Post.objects.create(
            text="Ivan text",
            author=self.user_ivan,
            group=self.group,
        )

        # Василием подписаться на Пупкина
        Follow.objects.create(user=self.user_vasya, author=self.user_pupkin)
        # Василием открыть ленту избранных авторов
        response = self.authorized_client_vasya.get(reverse("follow_index"))

        # Проверить наличие поста Пупкина
        self.assertEqual(response.context['post'].text, pupkin_post.text)

        # Проверить отсутсвие поста Ивана
        self.assertNotEqual(response.context['post'].id, ivan_post.id)

    def test_comment_follow_post(self):
        """Только авторизированный пользователь может комментировать посты."""
        # Создать Василия
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
