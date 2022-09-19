from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User
from ..constants import AMOUNT_POST_CYCLE, POSTS_PAGE, CLS_CYCLE


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.auth_user = User.objects.create_user(username='TestAuthUser')
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(PostTests.auth_user)
        self.authorized_client_author.force_login(PostTests.author)

    def compare_posts(self, arg_1, arg_2):
        """Функция для сверки двух постов (text, id, author_id)"""
        return (self.assertEqual(arg_1.text, arg_2.text),
                self.assertEqual(arg_1.id, arg_2.id),
                self.assertEqual(arg_1.author.id, arg_2.author.id))

    def compare_group_posts(self, arg_1, arg_2):
        """Функция для сверки группы двух постов"""
        return (self.assertEqual(arg_1.group.id, arg_2.group.id))

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        page_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in page_names_templates.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_uses_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, self.post)

    def test_group_posts_uses_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context['page_obj'][0]
        group = response.context['group']
        self.assertEqual(post, self.post)
        self.assertEqual(group, self.group)

    def test_profile_uses_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.post.author})
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post, self.post)
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context['post']
        self.assertEqual(post, self.post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create_page сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_uses_correct_context(self):
        """Шаблон редактирования поста create_post сформирован
        с правильным контекстом.
        """
        url = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        response = self.authorized_client_author.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        is_edit = response.context['is_edit']
        self.assertTrue('is_edit')
        self.assertIsInstance(is_edit, bool)
        post_id = response.context.get('post_id')
        self.assertEqual(post_id, self.post.pk)

    def test_post_appear_index_group_profile(self):
        """Проверка на отображение поста первым
        элементом на главной странице, на вкладке
        группы, в профиле пользователя
        """
        self.post_last = Post.objects.create(
            author=self.user,
            text=f'Тестовая запись #{self.post}',
            group=PostTests.group,)

        url = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': PostTests.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostTests.user.username}),
        )
        for adress in url:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                first_object = response.context['page_obj'][0]
                self.compare_posts(first_object, self.post_last)
                self.compare_group_posts(first_object, self.post_last)

    def test_post_not_another_group(self):
        """Созданный пост не попал в чужую группу"""
        another_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-another-slug',
            description='Тестовое описание дополнительной группы',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': another_group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.auth_user = User.objects.create_user(username='TestAuthUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = [
            Post(
                author=cls.author,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )
            for i in range(CLS_CYCLE)
        ]
        Post.objects.bulk_create(cls.posts)

    def test_first_page_contains_ten_records(self):
        """Количество постов на страницах index, group_list, profile
        равно 10.
        """
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ),
        )
        for url in urls:
            response = self.client.get(url)
            amount_posts = len(response.context.get('page_obj').object_list)
            self.assertEqual(amount_posts, POSTS_PAGE)

    def test_second_page_contains_three_records(self):
        """На страницах index, group_list, profile
        должно быть по три поста.
        """
        urls = (
            reverse('posts:index') + '?page=2',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2',
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ) + '?page=2',
        )
        for url in urls:
            response = self.client.get(url)
            amount_posts = len(response.context.get('page_obj').object_list)
            self.assertEqual(amount_posts, AMOUNT_POST_CYCLE)
