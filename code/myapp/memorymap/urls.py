from django.urls import path
from .views import (
    HomeView, 
    NewsFeedView,
    PostCreateView,
    PostDetailView,
    CommentDetailView,
    PostUpdateView,
    PostDeleteView,
    like_post,
    search_posts,
)


app_name = 'memorymap'

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('news_feed/', NewsFeedView.as_view(), name='news_feed'),
    path('<str:username>/post/create/', PostCreateView.as_view(), name='post_create'),
    path('<str:username>/post/<uuid:uuid>/', PostDetailView.as_view(), name='post_detail'),
    path('<str:username>/post/<uuid:uuid>/comment/<int:pk>/', CommentDetailView.as_view(), name='comment_detail'),
    path('<str:username>/post/<uuid:uuid>/update/', PostUpdateView.as_view(), name='post_update'),
    path('<str:username>/post/<uuid:uuid>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('post/<uuid:uuid>/like/', like_post, name='like_post'),
    path('search/', search_posts, name='search_posts'),
]