"""
URL configuration for sistema_turnos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='core:dashboard', permanent=False)),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('agenda/', include('agenda.urls')),
    path('agenda/disponibilidades/', include('disponibilidad.urls')),
    path('agenda/excepciones/', include('excepcion.urls')),
    path('clientes/', include('clientes.urls')),
    path('configuracion/', include('configuracion_negocio.urls')),
    path('configuracion-negocio/', RedirectView.as_view(pattern_name='configuracion_negocio:lista', permanent=False)),
    path('dashboard/', include('core.urls')),
    path('disponibilidad/', RedirectView.as_view(pattern_name='disponibilidades:lista', permanent=False)),
    path('excepcion/', RedirectView.as_view(pattern_name='excepciones:lista', permanent=False)),
    path('negocios/', include('negocio.urls')),
    path('negocio/', RedirectView.as_view(pattern_name='negocios:lista', permanent=False)),
    path('profesionales/', include('profesional.urls')),
    path('profesional/', RedirectView.as_view(pattern_name='profesionales:lista', permanent=False)),
    path('', include('reservas.urls')),
    path('servicios/', include('servicio.urls')),
    path('servicio/', RedirectView.as_view(pattern_name='servicios:lista', permanent=False)),
    path('sucursales/', include('sucursal.urls')),
    path('sucursal/', RedirectView.as_view(pattern_name='sucursales:lista', permanent=False)),
    path('turnos/', include('turnos.urls')),
    path('usuarios/', include('usuarios.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
