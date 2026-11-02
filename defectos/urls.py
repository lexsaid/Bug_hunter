from django.urls import path
from . import views

app_name = 'defectos'

urlpatterns = [
    path('', views.lista_defectos, name='lista'),
    path('nuevo/', views.crear_defecto, name='crear'),
    path('resolver/<int:defecto_id>/', views.resolver_defecto, name='resolver'),
    path(
        'proyecto/<int:project_id>/',
        views.lista_defectos,
        name='proyecto_lista',
    ),
    path(
        'proyecto/<int:project_id>/nuevo/',
        views.crear_defecto,
        name='proyecto_crear',
    ),
    path(
        'proyecto/<int:project_id>/resolver/<int:defecto_id>/',
        views.resolver_defecto,
        name='proyecto_resolver',
    ),
]