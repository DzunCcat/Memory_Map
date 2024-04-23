from django.urls import path
from .views import (
    HomeView, 
    LoginView, 
    LogoutView, 
    RegisterView, 
    ProfileView, 
    NewsFeedView,
    PostCreateView,
    PostDetailView,
    CommentDetailView,
    PostUpdateView,
    PostDeleteView,
)


app_name = 'memorymap'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('<slug:username>/profile/', ProfileView.as_view(), name='profile'),
    path('news_feed/', NewsFeedView.as_view(), name='news_feed'),
    path('<slug:username>/post/create/', PostCreateView.as_view(), name='post_create'),
    path('<slug:username>/post/<uuid:uuid>/', PostDetailView.as_view(), name='post_detail'),
    path('<slug:username>/post/<uuid:uuid>/comment/<int:pk>/', CommentDetailView.as_view(), name='comment_detail'),
    path('<slug:username>/post/<uuid:uuid>/update/', PostUpdateView.as_view(), name='post_update'),
    path('<slug:username>/post/<uuid:uuid>/delete/', PostDeleteView.as_view(), name='post_delete'),
]