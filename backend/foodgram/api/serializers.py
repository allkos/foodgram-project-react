from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from api.validators import (
    validate_cooking_time,
    validate_ingredients,
    validate_subscribed,
    validate_tags
)

from users.models import User, Subscription
from recipes.models import (
    IngredientRecipe,
    ShoppingCart,
    Ingredient,
    Favorite,
    Recipe,
    Tag
)


class UserCreateSerializerCustom(UserCreateSerializer):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")

        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'required': True},
        }


class UserSerializerCustom(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "is_subscribed")

    lookup_field = 'username'

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Subscription.objects.filter(
                user=user, author=obj.id
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class BriefInfoSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class IngredientAddSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    id = serializers.IntegerField(source='ingredient.id', read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    username = serializers.ReadOnlyField(source='author.username')
    recipes = serializers.SerializerMethodField()
    id = serializers.ReadOnlyField(source='author.id')

    class Meta:
        model = Subscription
        fields = ("id", "username", "first_name", "last_name", "is_subscribed", "recipes", 'recipes_count')

    def validate(self, data):
        request_user = self.context["request"].user
        data = validate_subscribed(data, request_user)
        return data

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=self.context["request"].user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        recipes_limit = (
            self.context["request"].query_params.get("recipes_limit")
        )
        queryset = (
            obj.author.recipes.all()[:int(recipes_limit)] if recipes_limit
            else obj.author.recipes.all()
        )
        return BriefInfoSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserSerializerCustom(read_only=True)
    cooking_time = serializers.IntegerField(
        validators=[validate_cooking_time]
    )
    ingredients = IngredientAddSerializer(
        many=True,
        validators=[validate_ingredients]
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        validators=[validate_tags]
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "author", "ingredients", "tags", "image", "name", "text", "cooking_time")

    def validate(self, data):
        ingredients = data["ingredients"]
        ingredient_list = []
        for item in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=item["id"]
            )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    f"Ингредиент - {ingredient} - уже есть в рецепте."
                )
            ingredient_list.append(ingredient)
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredient_list = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=get_object_or_404(
                    Ingredient, id=ingredient.get("id")
                ),
                amount=ingredient.get("amount")
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(
            author=self.context["request"].user,
            **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = validated_data.pop("tags")
        instance.tags.set(tags)
        instance.ingredients.clear()
        ingredients = validated_data.pop("ingredients")
        self.create_ingredients(ingredients, instance)
        return super().update(
            instance,
            validated_data
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context=self.context
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializerCustom(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IngredientRecipeSerializer(
        source="ingredientrecipe",
        many=True,
    )

    class Meta:
        model = Recipe
        fields = ("id", "tags", "author", "ingredients", "is_favorited", "is_in_shopping_cart", "name", "image", "text", "cooking_time")

    def get_ingredients(self, obj):
        ingredients_list = IngredientRecipe.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(ingredients_list, many=True).data

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request.user.is_authenticated:
            return obj.carts.filter(user=request.user).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = "__all__"

    def to_representation(self, instance):
        return BriefInfoSerializer(
            instance.recipe,
            context={"request": self.context.get("request")}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = "__all__"

    def to_representation(self, instance):
        return BriefInfoSerializer(
            instance.recipe,
            context={"request": self.context.get("request")}
        ).data
