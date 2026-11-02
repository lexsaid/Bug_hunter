from django.urls import path
from . import views

app_name = "proyectos"

urlpatterns = [
    path("", views.project_list, name="lista_proyectos"),
    path("crear/", views.create_project, name="crear_proyecto"),
    path("<int:project_id>/", views.project_detail, name="detalle_proyecto"),
    path(
        "<int:project_id>/checklist/",
        views.view_checklist,
        name="view_checklist",
    ),
    path(
        "<int:project_id>/reporte/",
        views.project_health_report,
        name="health_report",
    ),
    path(
        "<int:project_id>/reporte/pdf/",
        views.export_health_report_pdf,
        name="export_health_report_pdf",
    ),
]
