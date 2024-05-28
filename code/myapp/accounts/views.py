from django.urls import reverse_lazy
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse

from django.template.loader import render_to_string
from django.views.generic import TemplateView, CreateView, ListView

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import User, Follower
from memorymap.models import Post
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
    is_following = Follower.objects.filter(follower=request.user, followed=followed_user).exists()
    follower_count = Follower.objects.filter(followed=followed_user).count()
    following_count = Follower.objects.filter(follower=followed_user).count()
    return JsonResponse({'status': 'success', 'is_following': is_following, 'follower_count': follower_count, 'following_count': following_count})

@login_required
def unfollow(request, username):
    followed_user = get_object_or_404(User, username=username)
    Follower.objects.filter(follower=request.user, followed=followed_user).delete()
    is_following = Follower.objects.filter(follower=request.user, followed=followed_user).exists()
    follower_count = Follower.objects.filter(followed=followed_user).count()
    following_count = Follower.objects.filter(follower=followed_user).count()
    return JsonResponse({'status': 'success', 'is_following': is_following, 'follower_count': follower_count, 'following_count': following_count})

def hover_card(request, username):
    user = get_object_or_404(User, username=username)
    is_following = request.user.is_authenticated and Follower.objects.filter(follower=request.user, followed=user).exists()
    print(f"Hover card view called. User: {user.username}, Is following: {is_following}")  # デバッグ用
    context = {
        'user': user,
        'is_following': is_following,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('accounts/hover_card.html', context, request=request)
        return JsonResponse({'status': 'success', 'html': html})
    return render(request, 'accounts/hover_card.html', context)


class FollowingListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/following_list.html'
    context_object_name = 'following'

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return user.following.all()

class FollowersListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/followers_list.html'
    context_object_name = 'followers'

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return user.followers.all()