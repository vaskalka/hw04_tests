from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post

TEST_OF_PAGI_1: int = 10
TEST_OF_PAGI_2: int = 3
User = get_user_model()


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )

        cls.posts = [
            Post(
                author=cls.author,
                text='test_post',
                group=cls.group
            ) for i in range(1, 14)
        ]
        Post.objects.bulk_create(cls.posts)

        cls.templates = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list',
                       kwargs={'slug': f'{cls.group.slug}'}),
            3: reverse('posts:profile',
                       kwargs={'username': f'{cls.author.username}'})
        }

    def test_first_page_contains_ten_records(self):
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i])
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), TEST_OF_PAGI_1)

    def test_second_page_contains_three_records(self):
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i] + '?page=2')
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), TEST_OF_PAGI_2)


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)
        cls.not_author = User.objects.create_user(
            username='test_not_author'
        )
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.not_author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )
        cls.templ_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list',
                    kwargs={'slug': f'{cls.group.slug}'}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': f'{cls.author.username}'}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{cls.post.id}'}):
                        'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{cls.post.id}'}):
                        'posts/create_post.html',
        }

        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

    def test_page_uses_correct_template(self):
        for reverse_name, template in PostsPagesTests.templ_names.items():
            with self.subTest(template=template):
                response = PostsPagesTests.auth_author_client.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)

    def test_post_create_correct_context(self):
        response = PostsPagesTests.auth_author_client.get(
            reverse('posts:post_create')
        )
        for value, expected in PostsPagesTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        response = PostsPagesTests.auth_author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'})
        )
        for value, expected in PostsPagesTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_correct_context(self):
        response = PostsPagesTests.auth_author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
