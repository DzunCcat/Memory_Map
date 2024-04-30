from django.urls import reverse_lazy
from django.shortcuts import redirect, render, get_object_or_404

from django.views.generic import TemplateView, CreateView

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import User
from memorymap.models import Post, Follower
from .forms import CustomUserCreationForm, ProfileEditForm

class LoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('memorymap:home')

class LogoutView(LogoutView):
    next_page = '/accounts/login/'

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

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
    
@login_required
def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile', username=user.username)
    else:
        form = ProfileEditForm(instance=user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def follow(request, username):
    followed_user = get_object_or_404(User, username=username)
    if request.user != followed_user:
        Follower.objects.get_or_create(follower=request.user, followed=followed_user)
    return redirect('accounts:profile', username=username)

@login_required
def unfollow(request, username):
    followed_user = get_object_or_404(User, username=username)
    Follower.objects.filter(follower=request.user, followed=followed_user).delete()
    return redirect('accounts:profile', username=username)
