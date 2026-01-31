from django.shortcuts import render
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm


class AboutView(TemplateView):
    """Страница 'О проекте'."""

    template_name = 'pages/about.html'


class RulesView(TemplateView):
    """Страница с правилами."""

    template_name = 'pages/rules.html'


class RegistrationView(CreateView):
    """Страница регистрации."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('blog:index')


def csrf_failure(request, reason=''):
    """Обработчик ошибки 403 CSRF."""
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception):
    """Обработчик ошибки 404."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Обработчик ошибки 500."""
    return render(request, 'pages/500.html', status=500)


