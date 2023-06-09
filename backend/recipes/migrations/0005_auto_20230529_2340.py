# Generated by Django 3.2 on 2023-05-29 20:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0004_auto_20230517_2015'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='ingredientinrecipesamount',
            name='amount_ingredient',
        ),
        migrations.RenameField(
            model_name='recipe',
            old_name='indgredients',
            new_name='ingredients',
        ),
        migrations.AlterField(
            model_name='favoritereceipe',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_recipes', to='recipes.recipe', verbose_name='Рецепты'),
        ),
        migrations.AlterField(
            model_name='favoritereceipe',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_user', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='text',
            field=models.TextField(verbose_name='Описание рецепта'),
        ),
        migrations.AddConstraint(
            model_name='ingredientinrecipesamount',
            constraint=models.UniqueConstraint(fields=('recipe', 'ingredient'), name='unique_ingredient'),
        ),
    ]
