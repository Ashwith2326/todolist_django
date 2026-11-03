from django.db import IntegrityError, transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import urlencode
from django.views.decorators.http import require_POST
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView,FormView
from django.urls import reverse_lazy
from .models import Task
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm


# @login_required
class login(LoginView):
    # model = Task
    template_name = 'tasks_app/login.html'
    fields = ['username', 'password']
    redirect_authenticated_user=True
    
    def get_success_url(self):
        return reverse_lazy('task-list') 


# @register_required
class RegisterView(FormView):
    template_name = 'tasks_app/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user=True
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        try:
            # Keep the insert atomic so a simultaneous registration with the
            # same username can be reported as a form error instead of a 500.
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            username = form.cleaned_data.get('username', '')
            if not username or not form._meta.model.objects.filter(
                username__iexact=username
            ).exists():
                raise
            form.add_error('username', 'A user with that username already exists.')
            return self.form_invalid(form)

        return super().form_valid(form)


# @login_required
class logout(LogoutView):
    # model = Task
    template_name = 'tasks_app/logout.html'


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = 'tasks'
    template_name = 'tasks_app/task_list.html'

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        self.search_input = self.request.GET.get('search', '').strip()
        if self.search_input:
            queryset = queryset.filter(title__icontains=self.search_input)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['count'] = context['tasks'].filter(complete=False).count()
        context['completed_count'] = context['tasks'].filter(complete=True).count()
        context['total_count'] = context['tasks'].count()
        context['search_input'] = self.search_input
        return context


@login_required
@require_POST
def toggle_task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.complete = not task.complete
    task.save(update_fields=['complete'])

    search_input = request.POST.get('search', '').strip()
    task_list_url = reverse_lazy('task-list')
    if search_input:
        return redirect(f'{task_list_url}?{urlencode({"search": search_input})}')
    return redirect(task_list_url)



class Tasksdetail(LoginRequiredMixin, DetailView):
    model = Task
    context_object_name = 'task'
    template_name = 'tasks_app/detail.html'


class TasksCreate(LoginRequiredMixin, CreateView):
    model = Task
    fields = ['title', 'description', 'complete']
    # fields = '__all__'
    success_url = reverse_lazy('task-list')
    template_name = 'tasks_app/task_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(TasksCreate, self).form_valid(form)

class TasksUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    fields = ['title', 'description', 'complete']
    success_url = reverse_lazy('task-list')

# class TasksDelete(DeleteView):
#     model = Task
#     context_object_name = 'task'
#     success_url = reverse_lazy('task-list')

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks_app/task_delete.html'
    success_url = reverse_lazy('task-list')
