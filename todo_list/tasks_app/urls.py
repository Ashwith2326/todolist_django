
from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    RegisterView,
    TaskDeleteView,
    TaskListView,
    TasksCreate,
    TasksUpdate,
    Tasksdetail,
    toggle_task_complete,
)

urlpatterns = [
    path('login/',LoginView.as_view(template_name='tasks_app/login.html'),name='login'),
    path('logout/', LogoutView.as_view(template_name='tasks_app/logout.html'), name='logout'),
    path('register/', RegisterView.as_view(template_name='tasks_app/register.html'), name='register'),

    path('', TaskListView.as_view(), name='task-list'),
    path('task/<int:pk>/toggle-complete/', toggle_task_complete, name='task-toggle-complete'),
    path('task/<int:pk>/', Tasksdetail.as_view(), name='task-detail'),
    path('task-create/', TasksCreate.as_view(), name='task-create'),
    path('task-update/<int:pk>/', TasksUpdate.as_view(), name='task-update'),
    path('task-delete/<int:pk>/', TaskDeleteView.as_view(), name='task-delete'),
    
]