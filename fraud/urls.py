# fraud/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <-- IMPORTANT: ADD THIS IMPORT
from django.conf.urls.static import static # <-- IMPORTANT: ADD THIS IMPORT

urlpatterns = [
    path('', include('auditor.urls')),
    path('admin/', admin.site.urls),
    
]

# ONLY ADD THESE LINES FOR DEVELOPMENT
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # The following line for STATIC_URL is useful if you have project-level static files
    # that are not in an app's static folder, and STATIC_ROOT is configured.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)