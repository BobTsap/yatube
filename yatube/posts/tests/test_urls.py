from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_unknown = User.objects.create_user('Unknown')
        cls.user_author = User.objects.create_user('Author')
        cls.group = Group.objects.create(
            slug='slug',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_unknown = Client()
        self.authorized_client_author.force_login(self.user_author)
        self.authorized_client_unknown.force_login(self.user_unknown)

    def test_urls_exist_pages(self):
        """smoke test."""
        urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user_author.username}/',
            f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/edit/',
            '/create/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user_author.username}/',
            f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/edit/',
            '/create/',
        ]
        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        ]
        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница /posts/{self.post.id}/edit/ перенаправит анонимного
        читателя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница /create/ перенаправит анонимного
        читателя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_edit_url_redirect_not_author_on_post(self):
        """Страница /posts/{self.post.id}/edit/ перенаправит
         не автора поста на страницу поста.
        """
        response = self.authorized_client_unknown.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_unexisting_page_url_exception(self):
        """Страница /unexisting_page/ вызовет ошибку 404.
        """
        response = self.guest_client.get('/unexisting_page/', follow=True)
        self.assertEqual(response.status_code, 404)
