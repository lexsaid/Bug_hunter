from django.urls import path

from . import views

app_name = "checklist"

urlpatterns = [
    path("", views.lista_checklists, name="lista"),
    path("nuevo/", views.crear_checklist, name="crear"),
    path("<int:pk>/editar/", views.editar_checklist, name="editar"),
    path("<int:pk>/evaluar/", views.evaluar_checklist, name="evaluar"),
    path("<int:pk>/", views.detalle_checklist, name="detalle"),
]
