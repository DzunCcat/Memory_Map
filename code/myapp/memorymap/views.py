from django.shortcuts import render,redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Post, Media, Like, PostAccess
from .forms import  PostForm

from accounts.models import  Follower

from django.db.models import Q

from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST
from django.http import Http404, JsonResponse
from django.core.exceptions import ValidationError

from mptt.utils import get_cached_trees
from django.template.loader import render_to_string


class HomeView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'memorymap/home.html'
    context_object_name = 'posts'
    login_url = '/accounts/login/'

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.filter(
            Q(visibility="public") |
            Q(visibility="private", author=user) |
            Q(visibility="custom", author=user)
        ).order_by('-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        posts = context['posts']
        user = self.request.user

        for post in posts:
            post.author.is_following = Follower.objects.filter(follower=user, followed=post.author).exists()

        followers = Follower.objects.filter(followed=user).count()
        following = Follower.objects.filter(follower=user).count()

        context.update({
            'followers_count': followers,
            'following_count': following,
            'user': user,
        })

        # デバッグ用
        print(context)

        return context

    
class NewsFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'memorymap/news_feed.html'
    context_object_name = 'posts'
    login_url = '/accounts/login/'

    def get_queryset(self):
        following_users = self.request.user.following.values_list('followed', flat=True)
        update_interval = timezone.now() - timezone.timedelta(hours=1)
        seen_posts = PostAccess.objects.filter(user=self.request.user).values_list('post', flat=True)
        liked_posts = Like.objects.filter(user=self.request.user).values_list('post', flat=True)

        queryset = Post.objects.filter(
                    Q(created_at__gte=update_interval),
                    Q(author__in=following_users) | Q(author=self.request.user),
                    ~Q(id__in=seen_posts) | Q(id__in=liked_posts)
                ).order_by('-created_at')

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context['posts']
        user = self.request.user

        for post in posts:
            post.is_following = Follower.objects.filter(follower=user, followed=post.author).exists()

        followers = Follower.objects.filter(followed=user).count()
        following = Follower.objects.filter(follower=user).count()

        context.update({
            'followers_count': followers,
            'following_count': following,
            'user': user,
        })

        return context
    

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'memorymap/post_form.html'
    success_url = reverse_lazy('memorymap:home')  # Homeページにリダイレクト

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.author = self.request.user
            self.object.save()

            file_ids = [file_id for file_id in self.request.POST.get('file_ids', '').split(',') if file_id]

            media_files = Media.objects.filter(id__in=file_ids, user=self.request.user, post__isnull=True)
            for file in media_files:
                file.post = self.object
                file.save()
            Media.objects.filter(user=self.request.user, post__isnull=True).delete()

            return self.form_valid(form)
        else:
            print("INFO : form is invalid")
            self.object = None
            return self.form_invalid(form)
        
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'content_type' in form.fields:
            form.fields['content_type'].widget.attrs.update({'onchange': 'updateFormFields();'})
        return form

@require_POST
@login_required
def file_upload(request):
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        # ファイルタイプと大きさのバリデーション
        if uploaded_file.size > 5 * 1024 * 1024:  # 5MB
            return JsonResponse({'error': 'File size too large'}, status=400)
        
        allowed_types = ['image', 'video', 'audio']
        file_type = uploaded_file.content_type.split('/')[0]
        if file_type not in allowed_types:
            return JsonResponse({'error': 'Invalid file type'}, status=400)

        # ファイルの保存処理
        media = Media.objects.create(
            file=uploaded_file,
            user=request.user,
            media_type=file_type
        )
        return JsonResponse({'status': 'success', 'file_id': media.id})
    return JsonResponse({'status': 'error', 'error': 'No file uploaded'}, status=400)

@require_POST
@login_required
def delete_media(request):
    media_id = request.GET.get('media_id')
    media = get_object_or_404(Media, id=media_id)
    media.delete()
    return JsonResponse({'status': 'success'})

@require_POST
@login_required
def add_comment(request, uuid):
    parent_post = get_object_or_404(Post, uuid=uuid)
    form_data = request.POST.copy()
    form_data['content_type'] = 'tweet'  # コメントのデフォルトタイプを設定
    form_data['visibility'] = 'public'   # コメントのデフォルト可視性を設定
    form = PostForm(form_data)

    # debug
    print("Received data:", request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.parent = parent_post
        comment.content_type = 'tweet'

        # 親コメントがある場合、そのレベルに1を加える
        if 'parent_id' in request.POST:
            parent_comment = get_object_or_404(Post, id=request.POST.get('parent_id'))
            comment.parent = parent_comment
            comment.level = parent_comment.level + 1
        else:
            comment.level = parent_post.level + 1

        comment.save()

        # メディアファイルの処理
        file_ids = request.POST.get('file_ids', '').split(',')
        for file_id in file_ids:
            if file_id:
                try:
                    media = Media.objects.get(id=file_id, user=request.user, post__isnull=True)
                    media.post = comment
                    media.save()
                except Media.DoesNotExist:
                    pass  # エラーログを記録するなどの処理を追加できます

        # 不要なメディアファイルの削除
        Media.objects.filter(user=request.user, post__isnull=True).delete()

        # コメントのHTMLをレンダリング
        comment_html = render_to_string('memorymap/comment_item.html', {'comment': comment, 'user': request.user})
        
        return JsonResponse({
            'status': 'success',
            'html': comment_html,
            'comment_id': comment.id,
            'parent_id': comment.parent.id if comment.parent != parent_post else None,
        })
    else:
        # debug
        print("Form errors:", form.errors)  
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@require_POST
def edit_comment(request, comment_id):
    comment = get_object_or_404(Post, id=comment_id, author=request.user)
    original_parent = comment.parent
    original_level = comment.level
    form = PostForm(request.POST, instance=comment)
    # debug
    print("Received data:", request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        # 親子関係とレベル情報を保持
        comment.parent = original_parent
        comment.level = original_level
        comment.save()

                # コメントのHTMLを再レンダリング
        comment_html = render_to_string('memorymap/comment_item.html', {
            'comment': comment,
            'user': request.user,
            'post': comment.get_root()  # ルート投稿を取得
        })
        
        return JsonResponse({
            'status': 'success',
            'content': comment.content,
            'html': comment_html,
        })
    # debug
    print("Form errors:", form.errors)
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Post, id=comment_id, author=request.user)
    comment.delete()
    return JsonResponse({'status': 'success'})

class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'memorymap/post_detail.html'
    context_object_name = 'post'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['comment_form'] = PostForm(initial={'content_type': 'tweet'})
        context['comment_form'] = PostForm(initial={'content_type': 'tweet'})

        context['dropzone_config'] = {
            'url': reverse('memorymap:file_upload'),
            'maxFilesize': 10,
            'acceptedFiles': 'image/*,video/*,audio/*',
        }

        # コメントの取得方法を変更
        comments = self.object.get_descendants(include_self=False).filter(level__lte=3)
        context['comments'] = get_cached_trees(comments)
        
        context['like_count'] = self.object.likes.exclude(user=self.object.author).count()
        context['media'] = Media.objects.filter(post=self.object)

        post_access, created = PostAccess.objects.get_or_create(user=self.request.user, post=self.object)
        context['last_access_time'] = post_access.last_access_time
        context['is_new_visitor'] = created

        is_following = Follower.objects.filter(follower=self.request.user, followed=self.object.author).exists()
        context['is_following'] = is_following

        user = self.request.user
        post = self.object  # 現在の投稿を使用する

        followers = Follower.objects.filter(followed=user).count()
        following = Follower.objects.filter(follower=user).count()

        context.update({
            'followers_count': followers,
            'following_count': following,
            'user': user,
        })

        # debug
        print("Context data:", context)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.parent = self.object
            
            # 親コメントの処理を改善
            if 'parent_id' in request.POST:
                parent_comment = get_object_or_404(Post, id=request.POST.get('parent_id'))
                comment.parent = parent_comment
                comment.level = parent_comment.level + 1
            
            comment.content_type = 'tweet'
            comment.save()
            
            file_ids = [file_id for file_id in request.POST.get('file_ids', '').split(',') if file_id]
            media_files = Media.objects.filter(id__in=file_ids, user=request.user, post__isnull=True)
            for file in media_files:
                file.post = comment
                file.save()
            Media.objects.filter(user=request.user, post__isnull=True).delete()

            # Ajaxリクエストの場合は異なるレスポンスを返す
            if request.is_ajax():
                comment_html = render_to_string('memorymap/comment_item.html', {'comment': comment})
                return JsonResponse({'status': 'success', 'html': comment_html})

            return redirect(self.object.get_absolute_url())
        
        # フォームが無効な場合のAjax処理
        if request.is_ajax():
            return JsonResponse({'status': 'error', 'errors': form.errors})
        
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


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'memorymap/post_form.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    context_object_name = 'post'  # テンプレート内でオブジェクトを 'post' として参照できるようにする

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied('You do not have permission to edit this post.')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if self.object.parent:
            # リプライ（コメント）の場合、元の投稿の詳細ページにリダイレクト
            return reverse_lazy('memorymap:post_detail', kwargs={'username': self.object.parent.author.username, 'uuid': self.object.parent.uuid})
        else:
            # 通常の投稿の場合、ホームページにリダイレクト
            return reverse_lazy('memorymap:home')

class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'memorymap/post_confirm_delete.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    context_object_name = 'post'  # テンプレート内でオブジェクトを 'post' として参照できるようにする

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            raise PermissionDenied('You do not have permission to delete this post.')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if self.object.parent:
            # リプライ（コメント）の場合、元の投稿の詳細ページにリダイレクト
            return reverse_lazy('memorymap:post_detail', kwargs={'username': self.object.parent.author.username, 'uuid': self.object.parent.uuid})
        else:
            # 通常の投稿の場合、ホームページにリダイレクト
            return reverse_lazy('memorymap:home')
    

@login_required
def like_post(request, uuid):
    post = get_object_or_404(Post, uuid=uuid)
    if request.user != post.author:
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
    return redirect('memorymap:post_detail', username=post.author.username, uuid=post.uuid)

@login_required
def search_posts(request):
    query = request.GET.get('query', '')
    if query:
        posts = Post.objects.filter(
            (
                Q(title__icontains=query) |
                Q(content__icontains=query) | 
                Q(author__username__icontains=query) 
            ) & (
                Q(visibility = "public") |
                Q(visibility = "private", author=request.user) |
                Q(visibility = "custom", author=request.user) 
            )

            #Todo follower hashtag機能追加後
            # Q(visibility = "friends", author__in=request.user.following.all()) 
            # Q(hashtags__tag__icontains=query) |
            # Q(post_hashtags__hashtag__tag__icontains=query) 
        
        ).distinct()
    else:
        posts = []

    return render(request, 'memorymap/search_results.html', {'posts': posts, 'query': query})