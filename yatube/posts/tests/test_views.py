from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from django import forms

from ..models import Follow, Group, Post

User = get_user_model()


class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user('Author')
        cls.group = Group.objects.create(
            slug='slug',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user_author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:main_page'),
            url('posts:group_posts', slug=self.group.slug),
            url('posts:profile', username=self.user_author.username),
            url('posts:post_detail', post_id=self.post.id),
            url('posts:post_edit', post_id=self.post.id),
            url('posts:post_create'),
            'page_404/',

        ]
        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
            'core/404.html',
        ]

        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_exist_on_page(self):
        """Создав пост, пользователь увидит его на главной странице,
        на странице соответствующей группы, в своем профайле
        и на странице поста"""
        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

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

        post = Post.objects.create(
            author=self.user_author,
            group=self.group,
            image=uploaded)

        response_pages = (
            self.client.get(url('posts:main_page')),
            self.client.get(url('posts:group_posts', slug=self.group.slug)),
            self.client.get(
                url('posts:profile', username=self.user_author.username)),
        )

        for response_page in response_pages:
            self.assertIn(
                post, response_page.context['page_obj'])

    def test_post_exist_on_post_page(self):
        """Создав пост, пользователь увидит его на странице поста"""
        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

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

        post = Post.objects.create(
            author=self.user_author,
            group=self.group,
            image=uploaded)

        response = self.client.get(
            url('posts:post_detail', post_id=self.post.id))

        post_text = {
            response.context['post'].group: self.group,
            response.context['post'].author: self.user_author.username,
            response.context['post'].image: uploaded,
        }
        for value, expected in post_text.items():
            self.assertEqual(post_text[value], expected)

    def test_post_added_correctly(self):
        """Создав пост мы не увидим его в другой группе"""
        post_1_count = Post.objects.filter(group=self.group).count()

        group_2 = Group(slug='slug_2').save()
        self.user_author_2 = User.objects.create_user('Author_2')

        post_2 = Post.objects.create(
            author=self.user_author_2,
            group=group_2,
        )
        profile_url = reverse(
            'posts:profile',
            kwargs={'username': self.user_author.username}
        )

        response_profile = self.client.get(profile_url)
        post_2_count = Post.objects.filter(group=self.group).count()

        self.assertEqual(post_2_count, post_1_count)
        self.assertNotIn(post_2, response_profile.context['page_obj'])

    def test_post_create_url_contains_post_and_group(self):
        """На странице создания поста поля формы
        содержат поля для текста статьи, выбора группы,
        загрузки изображения"""
        response = self.client.get(reverse('posts:post_create'))

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field, expected)

    def test_index_page_url_contains_post_and_group(self):
        """Создав пост (см `setUpClass`), увидим его на главной странице"""
        response = self.client.get(reverse('posts:main_page'))
        post = response.context['page_obj'][0]

        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.group, self.post.group)

    def test_group_posts_url_contains_post_and_group(self):
        """Создав пост, увидим его на странице соответствующей группы"""
        response = self.client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        post = response.context['page_obj'][0]
        group = response.context.get('group')

        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_profile_page_url_contains_post_and_group(self):
        """Создав пост, он появится в профиле его автора"""
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_author.username}))
        post = response.context['page_obj'][0]

        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

        self.assertEqual(
            response.context.get('count_posts'), 1)
        self.assertEqual(
            response.context.get('author'), self.user_author)

    def test_post_detail_url_contains_post(self):
        """Создав пост, сможем посмотреть его на странице этого поста"""
        post_detail_url = reverse('posts:post_detail',
                                  kwargs={'post_id': self.post.id})
        response = self.client.get(post_detail_url)
        post = response.context['post']

        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_cache_index(self):
        """Пост при удалении сохраняется в кеше"""
        self.post_cache = Post.objects.create(
            author=self.user_author,
            group=self.group,
        )
        url = reverse('posts:main_page')
        response_1 = self.client.get(url)
        self.assertContains(response_1, self.post_cache.text)
        self.post_cache.delete()
        response_2 = self.client.get(url)
        self.assertContains(response_2, self.post_cache.text)
        cache.clear()
        response_3 = self.client.get(url)
        self.assertNotEqual(response_1.content, response_3.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user('Author')
        cls.group = Group.objects.create(
            slug='slug',
        )

        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(group=cls.group,
                                  author=cls.user_author))
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user_author)

    def test_first_page_contains_ten_records(self):
        """Создав 13 постов (см. setUpClass),
        на главной странице, на странице группы и в профиле автора
        на первой странице увидим 10 постов"""
        urls = (
            reverse('posts:main_page'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                    'username': self.user_author.username}),
        )
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Создав 13 постов (см. setUpClass),
        на главной странице, на странице группы и в профиле автора
        на второй странице увидим 3 поста"""
        urls = (
            reverse('posts:main_page') + '?page=2',
            reverse('posts:group_posts', kwargs={
                    'slug': self.group.slug}) + '?page=2',
            reverse('posts:profile', kwargs={
                    'username': self.user_author.username}) + '?page=2',
        )
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                len(response.context['page_obj']), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user('User_author')
        cls.user_follower = User.objects.create_user('Follower')
        cls.user_not_follower = User.objects.create_user('Not_follower')

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user_follower)
        self.client_not_follower = Client()
        self.client_not_follower.force_login(self.user_not_follower)

    def test_following_unfollowing_author(self):
        """Подписка и отписка от автора"""
        follow_data = {
            'user': self.user_follower,
            'author': self.user_author,
        }
        url_redirect = reverse('posts:profile', kwargs={'username': self.user_author.username})
        response = self.client.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.user_author.username}),
            data=follow_data, follow=True)
        count_follow = Follow.objects.filter(user=self.user_follower).count()

        self.assertEqual(count_follow, 1)
        self.assertRedirects(response, url_redirect)

        response_unfollow = self.client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user_author.username}),
            data=follow_data, follow=True)
        
        count_follow = Follow.objects.filter(user=self.user_follower).count()

        self.assertEqual(count_follow, 0)
        self.assertRedirects(response_unfollow, url_redirect)

    def test_follow_added_correctly(self):
        """Подписка на втора появится только у подписчика"""
        follow_data = {
            'user': self.user_follower,
            'author': self.user_author,
        }
        self.client.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.user_author.username}),
            data=follow_data, follow=True)

        count_follow = Follow.objects.filter(user=self.user_follower).count()
        count_not_follow = Follow.objects.filter(user=self.user_not_follower).count()

        self.assertEqual(count_follow, 1)
        self.assertEqual(count_not_follow, 0)
        