from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# from django.shortcuts import HttpResponse

from recipes.models import (IngredientInRecipesAmount, FavoriteReceipe,
                            Ingredient, Recipe, ShoppingCart, Tag)
from users.models import Follow, User
from .filters import RecipeFilter
from .utils import shopping_cart_file
from .pagination import LimitPaginator
from .permission import OwnerOrReadOnly
from .serializers import (ShoppingListFavoiriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipesWriteSerializer,
                          RecipesReadSerializer, TagSerializer, UserSerializer)


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
        user = self.request.user
        queryset = Follow.objects.filter(user=user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'], detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        user = request.user
        # author = get_object_or_404(User, pk=pk)
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            # serializer = FollowSerializer(
            #                               data=request.data,
            #                               context={'request': request})
            # serializer.is_valid(raise_exception=True)
            # # serializer.save(user=user, author=author)
            # Follow.objects.create(user=user, author=author)
            # return Response(
            #     serializer.data, status=status.HTTP_201_CREATED)
            serializer = FollowSerializer(
                    Follow.objects.create(user=user, author=author),
                    context={'request': request},
                )
            return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
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
        print("ALARM"*100)
        print(self.request)
        return RecipesWriteSerializer

    def post_delete_recipe(self, request, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if request.method == 'POST':
            serializer = ShoppingListFavoiriteSerializer(recipe)
            if model.objects.filter(
                    user=user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                model.objects.create(
                    user=user, recipe=recipe
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if model.objects.filter(
                user=user, recipe=recipe
            ).exists():
                model.objects.get(
                    user=user, recipe=recipe
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'errors': 'Рецепт уже удален!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    
    @action(
        methods=['POST', 'DELETE'], detail=True,
        permission_class=(IsAuthenticated,),
    )
    def favorite(self, request, **kwargs):
        return self.post_delete_recipe(
            request, kwargs.pop('pk'), FavoriteReceipe)

    @action(
        methods=['POST', 'DELETE'], detail=True,
    )
    def shopping_cart(self, request, **kwargs):
        return self.post_delete_recipe(
            request, kwargs.pop('pk'), ShoppingCart)

    @action(
        methods=['GET'], detail=False,
        permission_class=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        # ingredients = IngredientInRecipesAmount.objects.filter(
        #     recipe__shopping_recipes__user=request.user
        # )
        # ingredients = ingredients.values(
        #     'ingredient__name', 'ingredient__measurement_unit'
        # )
        # ingredients = ingredients.annotate(amount_sum=Sum('amount'))
        # return shopping_cart_file(ingredients)
        ingredients = IngredientInRecipesAmount.objects.select_related(
            'recipe', 'ingredient'
        )
        ingredients = ingredients.filter(
            recipe__shopping_recipes__user=request.user
        )
        ingredients = ingredients.values(
            'ingredient__name', 'ingredient__measurement_unit'
        )
        ingredients = ingredients.annotate(amount_sum=Sum('amount'))
        ingredients = ingredients.order_by('ingredient__name')
        return shopping_cart_file(ingredients)

