from django_filters.rest_framework import filters, FilterSet
from rest_framework.filters import SearchFilter

from recipes.models import Ingredient, Recipe, Tag


class SearchIngredientFilter(SearchFilter):
    search_param = "name"

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        to_field_name="slug",
        field_name="tags__slug",
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ("is_in_shopping_cart", "is_favorited", "author", "tags")

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and self.request.user.is_authenticated:
            return queryset.filter(carts__user=user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset
