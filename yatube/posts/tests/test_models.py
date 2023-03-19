from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    def test_models_group_have_object_names(self):
        """У моделей метод __str__ возвращает значение title."""
        group = Group(title='Тест')
        self.assertEqual(group.title, str(group))

    def test_models_post_have_object_names(self):
        """У моделей метод __str__ обрезает текст поста до 15 символов"""
        post = Post(text="Короткий пост")
        self.assertEqual(str(post), "Короткий пост")

        long_post = Post(text="str сокращает text до первых 15 символов")
        self.assertEqual(str(long_post), 'str сокращает t')
