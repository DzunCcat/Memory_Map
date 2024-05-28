from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    LoginView, 
    LogoutView, 
    RegisterView, 
    ProfileView, 
    FollowingListView, 
    FollowersListView,
    profile_edit, 
    hover_card,
    follow, 
    unfollow,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/<username>/', ProfileView.as_view(), name='profile'),
    path('profile/edit/<username>/', profile_edit, name='profile_edit'),
    path('hover_card/<username>/', hover_card, name='hover_card'),
    path('following/<str:username>/', FollowingListView.as_view(), name='following_list'),
    path('followers/<str:username>/', FollowersListView.as_view(), name='followers_list'),
    path('follow/<username>/', follow, name='follow'),
    path('unfollow/<username>/', unfollow, name='unfollow'),
]