import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Comment, Group, Post
from posts.forms import PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user('Author')
        cls.group = Group.objects.create(
            slug='slug',
        )
        cls.form = PostForm()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user_author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст в форме',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Post.objects.count(), 1,
        )
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Текст в форме',
                author=self.user_author,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """При редактировании поста данные изменяются"""
        self.post = Post.objects.create(text='Изначальный текст поста',
                                        author=self.user_author,
                                        group=self.group)
        post_before = self.post

        self.group_2 = Group.objects.create(
            slug='slug-2',
        )
        form_data = {
            'text': 'Новый текст в форме',
            'group': self.group_2.id,
        }
        post_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        response = self.client.post(post_url,
                                    data=form_data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Post.objects.filter(
                group=self.group_2.id,
                author=self.user_author,
            ).exists()
        )
        self.assertEqual(post_before.id, self.post.id)


class CommentCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('Authorized')
        cls.group = Group.objects.create(
            slug='slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_not_authorized_client(self):
        """Комментировать посты может только авторизованный пользователь"""
        self.comment = Comment.objects.create(
            post_id=self.post.id,
            author=self.user,
        )
        self.assertEqual(
            Comment.objects.count(), 1,
        )
        form_data = {'text': 'Комментарий'}
        comment_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id},
        )

        self.guest_client.post(comment_url,
                               data=form_data,
                               follow=True)
        self.assertEqual(
            Comment.objects.count(), 1,
        )
