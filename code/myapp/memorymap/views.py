from django.urls import reverse_lazy
from django.views import generic
from .models import Category, Article

class IndexView(generic.ListView):
    model = Article

class DetailView(generic.DetailView):
    model = Article

class CreateView(generic.edit.CreateView):
    model = Article
    fields = '__all__'

class UpdateView(generic.edit.UpdateView):
    model = Article
    fields = '__all__'

class DeleteView(generic.edit.DeleteView):
    model = Article
    success_url = reverse_lazy('memorymap:index')
