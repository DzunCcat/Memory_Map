# from django.contrib import admin
# from django.urls import path, include
# from django.views.generic import RedirectView
# from django.conf import settings
# from django.conf.urls.static import static


# urlpatterns = [
#     path('memorymap/', include('memorymap.urls')),
#     path('admin/', admin.site.urls),
#     path('',  RedirectView.as_view(url='/memorymap/')),
#     path('accounts/', include('accounts.urls')),
#     path('accounts/', include('django.contrib.auth.urls')),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('memorymap/', include('memorymap.urls')),  # Include the myapp urls
    path('accounts/', include('accounts.urls')),  # Include the accounts urls
]