from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.project_list, name='project_list'),

    path('proyectos/crear/', views.create_project, name='create_project'),
    
    path('proyectos/<int:project_id>/checklist/', views.view_checklist, name='view_checklist'),

    path('proyectos/<int:project_id>/reporte/', views.project_health_report, name='health_report'),
    path('proyectos/<int:project_id>/reporte/pdf/', views.export_health_report_pdf, name='export_health_report_pdf'),
]

