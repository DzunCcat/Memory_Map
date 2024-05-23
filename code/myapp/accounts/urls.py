from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    LoginView, 
    LogoutView, 
    RegisterView, 
    ProfileView, 
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
    path('follow/<username>/', follow, name='follow'),
    path('unfollow/<username>/', unfollow, name='unfollow'),
]