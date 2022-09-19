from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User


class PostCreateFormTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста',
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.auth_user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostCreateFormTests.author)

    def test_create_post(self):
        """Валидная форма создает запись в Posts."""
        post_count = Post.objects.all()
        post_count_set = set(post_count)
        form_data = {
            'text': 'Введенный в форму текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile', kwargs={'username': self.auth_user.username}
            )
        )
        new_post = Post.objects.all()
        new_post_set = set(new_post)

        difference_sets_of_posts = new_post_set.difference(post_count_set)
        self.assertEqual(len(difference_sets_of_posts), 1)
        last_post = difference_sets_of_posts.pop()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.pk, form_data['group'])
        self.assertEqual(last_post.author, self.auth_user)

    def test_author_edit_post(self):
        """Валидная форма изменяет запись в Posts."""
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )

        form_data = {
            'text': 'Отредактированный в форме текст',
            'group': new_group.pk,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, form_data['text'])
        self.assertEqual(post_edit.group.pk, form_data['group'])
        self.assertEqual(
            post_edit.author,
            self.post.author,
            'ошибка с автором поста при редактировании'
        )
