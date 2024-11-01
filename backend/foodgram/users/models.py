from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=200,
        unique=True
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True
    )
    password = models.CharField(
        'Пароль',
        max_length=150
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия"
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
