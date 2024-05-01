
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

# from django.contrib.auth.views import LoginView, LogoutView
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from django.urls import reverse_lazy

from .models import Post, Media, Comment, Like
# from .models import Follower
from .forms import  PostForm, CommentForm
# from .forms import CustomUserCreationForm

from django.db.models import Q
from django.contrib.auth.decorators import login_required

class HomeView(LoginRequiredMixin,ListView):
    model = Post
    template_name = 'memorymap/home.html'
    context_object_name = 'posts'
    login_url  = '/accounts/login/'

# class LoginView(LoginView):
#     template_name = 'login.html'
#     redirect_authenticated_user = True

#     def get_success_url(self):
#         return reverse_lazy('home')

# class LogoutView(LogoutView):
#     next_page = '/login/'

# class RegisterView(CreateView):
#     form_class = CustomUserCreationForm
#     template_name = 'registration/register.html'
#     success_url = reverse_lazy('login')

# class ProfileView(LoginRequiredMixin, TemplateView):
#     template_name = 'profile.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = get_object_or_404(User, username=self.kwargs.get('username', self.request.user.username))

#         context.update({
#             'user': user,
#             'posts': Post.objects.filter(author=user).order_by('-created_at'),
#             'followers': Follower.objects.filter(followed=user).count(),
#             'following': Follower.objects.filter(follower=user).count(),
#             'is_following': self.request.user.is_authenticated and Follower.objects.filter(follower=self.request.user, followed=user).exists()
#         })
#         return context

class NewsFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'memorymap/news_feed.html'
    context_object_name = 'posts'
    login_url = '/login/'

    def get_queryset(self):
        return Post.objects.filter(
            Q(author__in=self.request.user.following.all()) | Q(author=self.request.user)
        ).order_by('-created_at')

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'memorymap/post_form.html'
    success_url = reverse_lazy('memorymap:home')  # Homeページにリダイレクト

    # old code
    # def form_valid(self, form):
    #     form.instance.author = self.request.user  # 投稿の作者を自動的に設定
    #     return super().form_valid(form)

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        return response

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file')
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.author = request.user
            self.object.save()

            for f in files:
                Media.objects.create(post=self.object, file=f)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'content_type' in form.fields:
            form.fields['content_type'].widget.attrs.update({'onchange': 'updateFormFields();'})
        return form

class PostDetailView(DetailView):
    model = Post
    template_name = 'memorymap/post_detail.html'
    context_object_name = 'post'
    slug_field = 'uuid'  
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()  # コメントフォームをコンテキストに追加
        context['comments'] = Comment.objects.filter(post=self.object).order_by('-created_at')  # コメントを新しいものから順に表示
        context['like_count'] = self.object.likes.exclude(user=self.object.author).count()
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
    template_name = 'memorymap/post_form.html'
    slug_field = 'uuid'  
    slug_url_kwarg = 'uuid'  
    success_url = reverse_lazy('memorymap:home')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied('You do not have permission to edit this post.')
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'memorymap/post_confirm_delete.html'
    slug_field = 'uuid'  
    slug_url_kwarg = 'uuid'  
    success_url = reverse_lazy('memorymap:home')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied('You do not have permission to delete this post.')
        return super().dispatch(request, *args, **kwargs)
    

@login_required
def like_post(request, uuid):
    post = get_object_or_404(Post, uuid=uuid)
    if request.user != post.author:
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
    return redirect('memorymap:post_detail', username=post.author.username, uuid=post.uuid)


def search_posts(request):
    query = request.GET.get('query', '')
    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) | 
            Q(author__username__icontains=query) 
            # Q(hashtags__tag__icontains=query) |
            # Q(post_hashtags__hashtag__tag__icontains=query) 
        
        ).distinct()
    else:
        posts = []

    return render(request, 'memorymap/search_results.html', {'posts': posts, 'query': query})