from django.urls import path
from .views import (
    HomeView, 
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
    path('news_feed/', NewsFeedView.as_view(), name='news_feed'),
    path('<slug:username>/post/create/', PostCreateView.as_view(), name='post_create'),
    path('<slug:username>/post/<uuid:uuid>/', PostDetailView.as_view(), name='post_detail'),
    path('<slug:username>/post/<uuid:uuid>/comment/<int:pk>/', CommentDetailView.as_view(), name='comment_detail'),
    path('<slug:username>/post/<uuid:uuid>/update/', PostUpdateView.as_view(), name='post_update'),
    path('<slug:username>/post/<uuid:uuid>/delete/', PostDeleteView.as_view(), name='post_delete'),
]