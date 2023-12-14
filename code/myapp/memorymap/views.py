from django.urls import reverse_lazy
from django.views import generic
from .models import Category, Article
from django.conf import settings
from django.shortcuts import render

class IndexView(generic.ListView):
    model = Article

class DetailView(generic.DetailView):
    model = Article
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        return context

def streetview(request, pk):
    return render(request, 'streetview.html')

class CreateView(generic.edit.CreateView):
    model = Article
    fields = '__all__'

class UpdateView(generic.edit.UpdateView):
    model = Article
    fields = '__all__'

class DeleteView(generic.edit.DeleteView):
    model = Article
    success_url = reverse_lazy('memorymap:index')
