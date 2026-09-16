from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('trainer-portal/', TemplateView.as_view(template_name='trainer_portal/dashboard.html'), name='trainer-portal'),
    path('portal/', TemplateView.as_view(template_name='trainer_portal/dashboard.html'), name='trainer-portal-short'),
    path('api/', include('api.urls')),
]

uploads_dir = os.path.join(settings.BASE_DIR, 'uploads')
urlpatterns += static('/uploads/', document_root=uploads_dir)
urlpatterns += static('/media/', document_root=uploads_dir)

