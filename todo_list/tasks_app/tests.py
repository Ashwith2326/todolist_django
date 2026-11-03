from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Task
from .views import RegisterView, TaskListView, toggle_task_complete


class RegisterViewTests(TestCase):
    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'password1': 'Safe-password-492!',
                'password2': 'Safe-password-492!',
            },
        )

        self.assertRedirects(
            response,
            reverse('login'),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            get_user_model().objects.filter(username='newuser').exists()
        )
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_registration_rejects_mismatched_passwords(self):
        request = RequestFactory().post(
            reverse('register'),
            data={
                'username': 'newuser',
                'password1': 'Safe-password-492!',
                'password2': 'Different-password-492!',
            },
        )
        response = RegisterView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('password2', response.context_data['form'].errors)
        self.assertFalse(
            get_user_model().objects.filter(username='newuser').exists()
        )


class TaskSearchTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='taskowner',
            password='Safe-password-492!',
        )
        other_user = user_model.objects.create_user(
            username='otheruser',
            password='Safe-password-492!',
        )
        Task.objects.create(user=self.user, title='Buy groceries')
        Task.objects.create(user=self.user, title='Read a book')
        Task.objects.create(user=other_user, title='Buy another item')
        self.client.force_login(self.user)

    def test_search_filters_tasks_by_title_for_current_user(self):
        request = RequestFactory().get(reverse('task-list'), {'search': 'BUY'})
        request.user = self.user
        response = TaskListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context_data['tasks'].values_list('title', flat=True)),
            ['Buy groceries'],
        )
        self.assertEqual(response.context_data['search_input'], 'BUY')


class TaskCompletionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='taskowner',
            password='Safe-password-492!',
        )
        self.other_user = user_model.objects.create_user(
            username='otheruser',
            password='Safe-password-492!',
        )
        self.task = Task.objects.create(user=self.user, title='Finish report')
        self.client.force_login(self.user)

    def test_completion_action_toggles_status_and_preserves_search(self):
        response = self.client.post(
            reverse('task-toggle-complete', args=[self.task.pk]),
            {'search': 'Finish report'},
        )

        self.task.refresh_from_db()
        self.assertTrue(self.task.complete)
        self.assertRedirects(
            response,
            f"{reverse('task-list')}?search=Finish+report",
            fetch_redirect_response=False,
        )

        self.client.post(reverse('task-toggle-complete', args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertFalse(self.task.complete)

    def test_user_cannot_complete_another_users_task(self):
        other_task = Task.objects.create(
            user=self.other_user,
            title='Private task',
        )

        request = RequestFactory().post(
            reverse('task-toggle-complete', args=[other_task.pk])
        )
        request.user = self.user

        with self.assertRaises(Http404):
            toggle_task_complete(request, other_task.pk)
        other_task.refresh_from_db()
        self.assertFalse(other_task.complete)
