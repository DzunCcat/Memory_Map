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


from django.shortcuts import render,redirect
from django.views.generic import TemplateView, ListView, CreateView

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin

from django.urls import reverse_lazy

from .models import User, Post
from .forms import CustomUserCreationForm

class HomeView(LoginRequiredMixin,ListView):
    model = Post
    template_name = 'home.html'
    context_object_name = 'posts'
    login_url  = '/login/'

class LoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    next_page = '/'

    # def get_success_url(self):
    #     return reverse_lazy('home')

class LogoutView(LogoutView):
    next_page = '/login/'

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = kwargs.get('username')
        user = User.objects.get(username=username)
        context['user'] = user
        context['posts'] = Post.objects.filter(author=user)
        return context
    
class NewsFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'news_feed.html'
    context_object_name = 'posts'
    login_url = '/login/'

    def get_queryset(self):
        return Post.objects.filter(author__in=self.request.user.followed.all())

class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['content', 'content_type', 'title', 'visibility', 'thumbnail']
    template_name = 'create_post.html'
    success_url = reverse_lazy('news_feed')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['content', 'content_type', 'visibility']
    template_name = 'post_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    
