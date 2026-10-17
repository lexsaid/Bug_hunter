from django.urls import path
from . import views

app_name = 'defectos'

urlpatterns = [
    path('', views.lista_defectos, name='lista'),
    path('nuevo/', views.crear_defecto, name='crear'),
    path('resolver/<int:defecto_id>/', views.resolver_defecto, name='resolver'),
]