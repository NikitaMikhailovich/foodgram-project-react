from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        help_text='Название тэга',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='HEX-код',
        help_text='HEX-код для обозначения цвета тэга',
        max_length=7,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        help_text='Имя для URL',
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name

    
class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Ингридиент',
        help_text='Название ингридиента',
        max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        help_text='Единица измерения количества ингридиента',
        max_length=200, 
    )
    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        help_text='Тэги по рецепту',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        help_text='Автор публикации рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )

    indgredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты',
        help_text='Ингридиенты для приготовления по рецепту',
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200)
    image = models.ImageField(
        'Фотография блюда',
        upload_to='recipes/',
    )
    text = models.TextField(

    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        help_text='Время приготовления блюда',
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.title
    

class IngredientInRecipesAmount(models.Model):
    amount = models.IntegerField(
        verbose_name='Количество',
        help_text='Необходимое количество данного ингридиента',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент',
    )

   
class FavoriteReceipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favoirite_user',
        verbose_name='Пользователь'
    )

    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favoirite_recipes',
        verbose_name='Рецепты',
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='favorite_recipe',
            )
        ]

class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_user',
        verbose_name='Пользователь'
    )

    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_recipes',
        verbose_name='Рецепты',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='recipe_in_shopping_cart',
            )
        ]