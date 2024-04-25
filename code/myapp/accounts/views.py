from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from memorymap.models import Post, Follower
from .forms import CustomUserCreationForm

class LoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('home')

class LogoutView(LogoutView):
    next_page = '/login/'

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs.get('username', self.request.user.username))

        context.update({
            'user': user,
            'posts': Post.objects.filter(author=user).order_by('-created_at'),
            'followers': Follower.objects.filter(followed=user).count(),
            'following': Follower.objects.filter(follower=user).count(),
            'is_following': self.request.user.is_authenticated and Follower.objects.filter(follower=self.request.user, followed=user).exists()
        })
        return context
