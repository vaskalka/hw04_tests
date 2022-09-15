import tempfile
import shutil

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test_title',
            slug='test-slug',
            description='Test_description'
        )

    def setUp(self):
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        count_posts = Post.objects.count()
        form_data = {
            'text': 'form_text',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertTrue(Post.objects.filter(
            text='form_text',
            group=self.group.id,
            author=self.user
        ).exists())
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': self.user}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        self.post = Post.objects.create(
            text='test_text',
            author=self.user,
            group=self.group
        )
        old_text = self.post
        self.group2 = Group.objects.create(
            title='Test_title_2',
            slug='test-slug_2',
            description='Test_description_2'
        )
        form_data = {
            'text': 'form_text_2',
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_text.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
            group=self.group2.id,
            author=self.user,
            pub_date=self.post.pub_date
        ).exists())

    def test_group(self):
        self.post = Post.objects.create(
            text='form_text',
            author=self.user,
            group=self.group
        )
        old_text = self.post
        form_data = {'text': 'form_text',
                     'group': ''}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_text.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(old_text.group, form_data['group'])
