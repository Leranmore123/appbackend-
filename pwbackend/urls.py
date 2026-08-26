from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('trainer-portal/', TemplateView.as_view(template_name='trainer_portal/dashboard.html'), name='trainer-portal'),
    path('portal/', TemplateView.as_view(template_name='trainer_portal/dashboard.html'), name='trainer-portal-short'),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
