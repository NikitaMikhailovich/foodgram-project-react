from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (IngredientInRecipesAmount, FavoriteReceipe,
                            Ingredient, Recipe, ShoppingCart, Tag)
from users.models import Follow, User
from .filters import RecipeFilter
from .pagination import LimitPaginator
from .permission import OwnerOrReadOnly
from .serializers import (ShoppingListFavoiriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipesWriteSerializer,
                          RecipesReadSerializer, TagSerializer, UserSerializer)


# Create your views here.

class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )


class UsersViewSet(UserViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        methods=['GET'], detail=False,
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitPaginator,
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
    
    @action(
        methods=['POST', 'DELETE'], detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def subsribe(self, request, pk):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            if user.pk == author.pk:
                return Response(
                    {'errors': 'Нельзя подписаться на себя!'},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = FollowSerializer(
                    request.data, context={'request': request}
                )
                if serializer.is_valid():
                    serializer.save(user=user, author=author)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
        Follow.objects.filter(user=user, author=author).delete()
        return Response('Успешная отписка', status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    permission_class = (OwnerOrReadOnly,)
    pagination_class = LimitPaginator

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipesReadSerializer
        return RecipesWriteSerializer

    @action(
        methods=['POST', 'DELETE'], detail=True,
        permission_class=(IsAuthenticated,),
    )
    def favoirite(self, request, **kwargs):

        recipe = get_object_or_404(Recipe, pk=kwargs.pop('pk'))
        if request.method == 'POST':
            serializer = ShoppingListFavoiriteSerializer(recipe)
            if FavoriteReceipe.objects.filter(
                    user=self.request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                FavoriteReceipe.objects.create(
                    user=self.request.user, recipe=recipe
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if FavoriteReceipe.objects.filter(
                user=self.request.user, recipe=recipe
            ).exists():
                FavoriteReceipe.objects.get(
                    user=self.request.user, recipe=recipe
                ).delete() 
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'errors': 'Рецепт уже удален!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
 
    @action(
        methods=['POST', 'DELETE'], detail=True,
    )
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs.pop('pk'))
        if request.method == 'POST':
            serializer = ShoppingListFavoiriteSerializer(recipe)
            if ShoppingCart.objects.filter(
                    user=self.request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                ShoppingCart.objects.create(
                    user=self.request.user, recipe=recipe
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if ShoppingCart.objects.filter(
                user=self.request.user, recipe=recipe
            ).exists():
                ShoppingCart.objects.get(
                    user=self.request.user, recipe=recipe
                ).delete() 
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'errors': 'Рецепт уже удален!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @action(
        methods=['GET'], detail=False,
        permission_class=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        ingredients = IngredientInRecipesAmount.objects.filter(
            recipe__shopping_recipes__user=user
        )
        ingredients = ingredients.values(
            'ingredient__name', 'ingredient__measurement_unit'
        )
        ingredients = ingredients.annotate(amount_sum=Sum('amount'))
        shopping_list = 'Список покупок: \n'
        for ingredient in ingredients:
            shopping_list += (
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["amount_sum"]} '
                f'({ingredient["ingredient__measurement_unit"]}) \n'
            )
            response = HttpResponse(
                shopping_list, content_type='text/plain; charset=utf8'
            )
            response[
                'Content-Disposition'
            ] = 'attachment; filename="shopping_cart.txt"'
        return response