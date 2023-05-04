import base64
from django.core.files.base import ContentFile
from rest_framework.serializers import (BooleanField,
                                        IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField, ImageField)
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from recipes.models import IngredientInRecipesAmount, Ingredient, Recipe, Tag
from users.models import User, Follow


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit', 
            )


class Base64ImageField(ImageField): 

    def to_internal_value(self, data): 
        if isinstance(data, str) and data.startswith('data:image'): 
            format, imgstr = data.split(';base64,') 
            ext = format.split('/')[-1] 
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext) 
        return super().to_internal_value(data)
    

class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )

class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return user.follower.filter(follower=obj).exists()

class UserCreateSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'username',
            'first_name', 'last_name', 'password',)

class ShoppingListFavoiriteSerializer(ModelSerializer):
    image = Base64ImageField(read_only=True)
    name = ReadOnlyField()
    cooking_time = ReadOnlyField()
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    
class FollowSerializer(ModelSerializer):
    email = ReadOnlyField(source='following.email')
    username = ReadOnlyField(source='following.username')
    first_name = ReadOnlyField(source='following.first_name')
    last_name = ReadOnlyField(source='following.last_name')
    id = ReadOnlyField(source='following.id')

    recipes = ShoppingListFavoiriteSerializer(many=True)
    recipes_count = SerializerMethodField()
    is_subscribed = SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        
        user = self.context.get('request').user
        if user is None or user.is_anonymous:
            return False
        return user.follower.filter(user=obj).exists()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        query_params = request.query_params 
        if 'recipes_limit' in query_params:
            recipes_limit = query_params['recipes_limit']
            data['recipes'] = data['recipes'][:int(recipes_limit)]
        return data
            
class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id'
            'name'
            'measurement_unit'
        )


class IngredientsInRecipeWriteSerializer(ModelSerializer):
    class Meta:
        model = IngredientInRecipesAmount
        fields = (
            'id',
            'amount',
        )


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )




class RecipesReadSerializer(ModelSerializer):
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    ingridients = IngredientSerializer(
        required=True, many=True
    )
    tags = TagSerializer(
        required=True, many=True
    )
    author = UserSerializer(
        required=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingridients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )
    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.favoirite_recipes.filter(user=user).exists()
        )
    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.shopping_recipes.filter(user=user).exists()
        )

class RecipesWriteSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = IngredientsInRecipeWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients'
            'tags'
            'image'
            'name'
            'text'
            'cooking_time'
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        user = self.context.get('request').user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.update(tags)
        for ingridient in ingredients:
            IngredientInRecipesAmount.objects.create(ingridient=ingridient.pop('id'), recipe=recipe, amount=ingridient.pop('amount'))
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.update(tags)
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        for ingridient in ingredients:
            IngredientInRecipesAmount.objects.create(ingridient=ingridient.pop('id'), recipe=instance, amount=ingridient.pop('amount'))
        return super().update(instance, validated_data)
