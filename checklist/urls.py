from django.urls import path

from . import views

app_name = "checklist"

urlpatterns = [
    path("", views.lista_checklists, name="lista"),
    path("nuevo/", views.crear_checklist, name="crear"),
    path(
        "proyecto/<int:project_id>/",
        views.lista_checklists,
        name="proyecto_lista",
    ),
    path(
        "proyecto/<int:project_id>/nuevo/",
        views.crear_checklist,
        name="proyecto_crear",
    ),
    path(
        "proyecto/<int:project_id>/<int:pk>/editar/",
        views.editar_checklist,
        name="proyecto_editar",
    ),
    path(
        "proyecto/<int:project_id>/<int:pk>/evaluar/",
        views.evaluar_checklist,
        name="proyecto_evaluar",
    ),
    path(
        "proyecto/<int:project_id>/<int:pk>/",
        views.detalle_checklist,
        name="proyecto_detalle",
    ),
    path("<int:pk>/editar/", views.editar_checklist, name="editar"),
    path("<int:pk>/evaluar/", views.evaluar_checklist, name="evaluar"),
    path("<int:pk>/", views.detalle_checklist, name="detalle"),
]
