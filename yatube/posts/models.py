from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField('Группа', unique=True)
    description = models.TextField('Текст, на странице сообщества')

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.title
        super().save(*args, **kwargs)


class Post(models.Model):
    text = models.TextField(help_text='Напишите что нибудь интересное')
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              related_name='posts', blank=True, null=True,
                              help_text='Выбирете группу публикации')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return f'{self.text[:15]}'

    class Meta:
        ordering = ['-pub_date']


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comment')
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comment')
    text = models.TextField(help_text='Оставьте комментарий')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f'{self.text[:10]}'

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = timezone.now()
        super().save(*args, **kwargs)


class Follow(models.Model):
    # ссылка на объект пользователя, который подписывается на меня
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    # ссылка на объект пользователя, на которого подписываюсь я
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')

    class Meta:
        # Защита от дубликатов
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='uniq_follow'
            ),
        ]
