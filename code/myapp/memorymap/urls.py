from django.urls import path
from .views import (
    HomeView, 
    NewsFeedView,
    PostCreateView,
    PostDetailView,
    PostUpdateView,
    PostDeleteView,
    like_post,
    search_posts,
    delete_media,
    file_upload,
    add_comment,
    edit_comment,
    delete_comment,
)


app_name = 'memorymap'

urlpatterns = [
    path('home/', HomeView.as_view(), name='home'),
    path('news_feed/', NewsFeedView.as_view(), name='news_feed'),
    path('<str:username>/post/create/', PostCreateView.as_view(), name='post_create'),
    path('<str:username>/post/<uuid:uuid>/', PostDetailView.as_view(), name='post_detail'),
    path('<str:username>/post/<uuid:uuid>/update/', PostUpdateView.as_view(), name='post_update'),
    path('<str:username>/post/<uuid:uuid>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('post/<uuid:uuid>/like/', like_post, name='like_post'),
    path('search/', search_posts, name='search_posts'),
    path('delete_media/', delete_media, name='delete_media'),
    path('api/upload/', file_upload, name='file_upload'),
    path('post/<uuid:uuid>/add_comment/', add_comment, name='add_comment'),
    path('comment/<int:comment_id>/edit/', edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
]