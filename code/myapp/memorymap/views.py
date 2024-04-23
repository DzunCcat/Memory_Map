
#version 0.1 code
# from django.urls import reverse_lazy
# from django.views import generic
# from .models import Category, Article
# from django.conf import settings
# from django.shortcuts import render
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.core.exceptions import PermissionDenied

# class IndexView(generic.ListView):
#     model = Article

# class DetailView(generic.DetailView):
#     model = Article
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
#         article = self.get_object()
#         # Google Maps ストリートビューのURLを構築
#         if article.latitude is not None and article.longitude is not None:
#             street_view_base_url = "https://maps.googleapis.com/maps/api/js?v=3.52"
#             street_view_params = f"&key={settings.GOOGLE_MAPS_API_KEY}&callback=initMap"
#             context['lat'] = article.latitude
#             context['lng'] = article.longitude
#             context['streetview_url'] = f"{street_view_base_url}?{street_view_params}"
#         return context

# def streetview(request, pk):
#     return render(request, 'streetview.html')

# class CreateView(LoginRequiredMixin, generic.edit.CreateView):
#     model = Article
#     fields = ['title','content','image','category',] #'__all__'

#     def form_valid(self, form):
#         form.instance.author = self.request.user
#         return super(CreateView, self).form_valid(form)

# class UpdateView(LoginRequiredMixin, generic.edit.UpdateView):
#     model = Article
#     fields = ['title','content','image','category',]#'__all__'

#     def dispatch(self, request, *args, **kwargs):
#         obj = self.get_object()
#         if obj.author != self.request.user:
#             raise PermissionDenied('You do not have permission to edit.')
#         return super(UpdateView, self).dispatch(request, *args, **kwargs)
    

# class DeleteView(LoginRequiredMixin, generic.edit.DeleteView):
#     model = Article

#     def dispatch(self, request, *args, **kwargs):
#         obj = self.get_object()
#         if obj.author != self.request.user:
#             raise PermissionDenied('You do not have permission to edit.')
#         return super(DeleteView, self).dispatch(request, *args, **kwargs)
    
#     success_url = reverse_lazy('memorymap:index')

#new code
from django.shortcuts import render,redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from django.urls import reverse_lazy

from .models import User, Post, Media, Follower, Comment
from .forms import CustomUserCreationForm, PostForm, CommentForm

class HomeView(LoginRequiredMixin,ListView):
    model = Post
    template_name = 'home.html'
    context_object_name = 'posts'
    login_url  = '/login/'

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

class NewsFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'news_feed.html'
    context_object_name = 'posts'
    login_url = '/login/'

    def get_queryset(self):
        return Post.objects.filter(author__in=self.request.user.followed.all())

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/post_form.html'
    success_url = reverse_lazy('home')  # Homeページにリダイレクト

    # old code
    # def form_valid(self, form):
    #     form.instance.author = self.request.user  # 投稿の作者を自動的に設定
    #     return super().form_valid(form)

    def form_valid(self, form):
        form.instance.author = self.request.user  # 投稿の作者を自動的に設定
        response = super(PostCreateView, self).form_valid(form)  # Postオブジェクトを保存
        media_files = self.request.FILES.getlist('media')  # フォームから送信されたメディアファイルを取得
        for file in media_files:
            Media.objects.create(post=self.object, file=file)  # 各メディアファイルを新しいMediaオブジェクトとして保存
        return response

    def get_form(self, form_class=None):
        form = super(PostCreateView, self).get_form(form_class)
        # フォームの動的設定
        if 'content_type' in form.fields:
            form.fields['content_type'].widget.attrs.update({'onchange': 'updateFormFields();'})
        return form

class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()  # コメントフォームをコンテキストに追加
        context['comments'] = Comment.objects.filter(post=self.object).order_by('-created_at')  # コメントを新しいものから順に表示
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.user = request.user  # コメント投稿者
            comment.save()
            return redirect(self.object.get_absolute_url())
        return self.get(request, *args, **kwargs)
    
class CommentDetailView(DetailView):
    model = Comment
    template_name = 'comment_detail.html'
    context_object_name = 'comment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ここで追加のコンテキストを設定する場合はここに書きます
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/post_form.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied('You do not have permission to edit this post.')
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'posts/post_confirm_delete.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied('You do not have permission to delete this post.')
        return super().dispatch(request, *args, **kwargs)