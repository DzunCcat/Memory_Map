from django.urls import reverse_lazy
from django.views import generic
from .models import Category, Article

class IndexView(generic.ListView):
    model = Article
