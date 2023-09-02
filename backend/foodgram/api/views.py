from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status

from api.filters import SearchIngredientFilter, RecipeFilter
from api.pagination import CustomPaginLimitOnPage
from users.models import Subscription, User
from api.permissions import (
    AuthorOrReadOnly,
    AdminOrReadOnly
)
from api.serializers import (
    ShoppingCartSerializer,
    SubscriptionSerializer,
    RecipeCreateSerializer,
    UserSerializerCustom,
    IngredientSerializer,
    RecipeReadSerializer,
    FavoriteSerializer,
    TagSerializer
)
from recipes.models import (
    IngredientRecipe,
    ShoppingCart,
    Ingredient,
    Favorite,
    Recipe,
    Tag
)


class UserViewSetCustom(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializerCustom
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPaginLimitOnPage
    lookup_field = 'id'

    @action(detail=True, methods=("POST", "DELETE",))
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            subscribe = Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                subscribe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = get_object_or_404(
            Subscription,
            user=user,
            author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=("GET",))
    def subscriptions(self, request):
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    pagination_class = CustomPaginLimitOnPage
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def create_list_of_products(self, ingredients):
        list_of_products = ["Купить в магазине:"]
        for ingredient in ingredients:
            ingredient_name = ingredient.get("ingredient__name", "")
            measurement_unit = ingredient.get(
                "ingredient__measurement_unit", ""
            )
            amount = ingredient.get("amount", "")
            list_of_products.append(
                f"{ingredient_name} ({measurement_unit}) - {amount}"
            )
        return "\n".join(list_of_products)

    @action(detail=False, methods=("GET",))
    def download_shopping_cart(self, request):
        ingredients = IngredientRecipe.objects.filter(
            recipe__carts__user=request.user
        ).order_by("ingredient__name").values(
            "ingredient__name",
            "ingredient__measurement_unit"
        ).annotate(amount=Sum('amount'))
        carts_content = self.create_list_of_products(ingredients)
        file_name = "list_of_products.txt"
        response = HttpResponse(
            carts_content,
            content_type='text/plain'
        )
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response

    @action(detail=True, methods=("POST",))
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {"recipe": recipe.id, "user": request.user.id}
        serializer = ShoppingCartSerializer(
            data=data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            ShoppingCart,
            recipe__id=pk,
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("POST",))
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {"recipe": recipe.id, "user": request.user.id}
        serializer = FavoriteSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            Favorite,
            recipe=get_object_or_404(Recipe, id=pk),
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (SearchIngredientFilter,)
    search_fields = ("^name",)
