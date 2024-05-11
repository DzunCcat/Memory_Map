
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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from django.urls import reverse_lazy

from .models import Post, Media, Comment, Like
from .forms import  PostForm, CommentForm

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.core.exceptions import ValidationError


class HomeView(LoginRequiredMixin,ListView):
    model = Post
    template_name = 'memorymap/home.html'
    context_object_name = 'posts'
    login_url  = '/accounts/login/'

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

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.author = self.request.user
            self.object.save()

            file_ids = self.request.POST.get('file_ids', '').split(',')
            file_ids = [file_id for file_id in file_ids if file_id]

            print("test:")
            print(file_ids)

            for file_id in file_ids:
                try:
                    file = Media.objects.get(id=file_id,user=self.request.user,post__isnull=True)
                    file.post = self.object 
                    file.save()
                except Media.DoesNotExist:
                    continue
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
        context['media'] = Media.objects.filter(post=self.object) 
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
    
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        uuid = self.kwargs.get('uuid')
        if uuid is not None:
            queryset = queryset.filter(uuid=uuid)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404("No post found matching the query")

        return obj
    

def delete_media(request):
        media_id = request.GET.get('media_id')
        media = get_object_or_404(Media, id=media_id)
        media.delete()
        return JsonResponse({'status': 'success'})



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

@login_required
def file_upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        media_type = request.POST.get('media_type', 'image')  # フォームからメディアタイプを受け取る

        try:
            uploaded_file = Media.objects.create(file=file, media_type=media_type, user=request.user)  # postは後で関連付け
            return JsonResponse({'status': 'success', 'file_id': uploaded_file.id}, status=201)
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': _('Invalid request')}, status=400)


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