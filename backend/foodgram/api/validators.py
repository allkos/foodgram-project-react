from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from users.models import Subscription


def validate_ingredients(value):
    if not value or value == 0:
        raise ValidationError(
            f"Количество ингредиентов не может быть пустым, "
            f"или быть равно {0}"
        )
    return value


def validate_tags(value):
    if not value:
        raise ValidationError('Укажите тег!')
    return value


def validate_cooking_time(value):
    if not value or value <= 1:
        raise ValidationError('Укажите время приготовления!')
    return value


def validate_amount(value):
    if not value or value < 1:
        raise ValidationError('Заполните ингридиентами!')
    return value


def validate_subscribed(data, request_user):
    author = data["author"]
    if request_user == author:
        raise serializers.ValidationError(
            "Вы не можете подписаться на самого себя!"
        )
    if Subscription.objects.filter(
        user=request_user, author=author
    ).exists():
        raise serializers.ValidationError(
            "Вы уже подписаны на этого автора!"
        )
    return data
