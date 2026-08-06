from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from Consultorias import views as cons_views

urlpatterns = [
    path('service-worker.js', cons_views.service_worker, name='service_worker'),
    path('sin-conexion/', cons_views.offline, name='offline'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', cons_views.logout_view, name='logout'),
    path('', include('Consultorias.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
