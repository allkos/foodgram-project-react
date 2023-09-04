from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSetCustom,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet
)


app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register('users', UserViewSetCustom, basename='user')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('recipes', RecipeViewSet, basename='recipe')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
]
