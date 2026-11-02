from django.urls import path
from . import views

app_name = 'matriz_trazabilidad'

urlpatterns = [
    path('', views.vista_matriz, name='vista_matriz'),
    path('rn/nuevo/', views.registrar_rn, name='registrar_rn'),
    path('<int:pk>/cu/nuevo/', views.registrar_cu, name='registrar_cu'),
    path('<int:pk>/rf/nuevo/', views.registrar_rf, name='registrar_rf'),
    path('<int:pk>/rnf/nuevo/', views.registrar_rnf, name='registrar_rnf'),
    path('<int:pk>/modulo/vincular/', views.vincular_modulo, name='vincular_modulo'),
    path('<int:pk>/pantalla/vincular/', views.vincular_pantalla, name='vincular_pantalla'),
    path('<int:pk>/cp/nuevo/', views.registrar_cp, name='registrar_cp'),
    path('<int:pk>/evidencia/agregar/', views.registrar_evidencia, name='registrar_evidencia'),
    path('proyecto/<int:project_id>/', views.vista_matriz, name='proyecto_lista'),
    path('proyecto/<int:project_id>/rn/nuevo/', views.registrar_rn, name='proyecto_registrar_rn'),
    path('proyecto/<int:project_id>/<int:pk>/cu/nuevo/', views.registrar_cu, name='proyecto_registrar_cu'),
    path('proyecto/<int:project_id>/<int:pk>/rf/nuevo/', views.registrar_rf, name='proyecto_registrar_rf'),
    path('proyecto/<int:project_id>/<int:pk>/rnf/nuevo/', views.registrar_rnf, name='proyecto_registrar_rnf'),
    path('proyecto/<int:project_id>/<int:pk>/modulo/vincular/', views.vincular_modulo, name='proyecto_vincular_modulo'),
    path('proyecto/<int:project_id>/<int:pk>/pantalla/vincular/', views.vincular_pantalla, name='proyecto_vincular_pantalla'),
    path('proyecto/<int:project_id>/<int:pk>/cp/nuevo/', views.registrar_cp, name='proyecto_registrar_cp'),
    path('proyecto/<int:project_id>/<int:pk>/evidencia/agregar/', views.registrar_evidencia, name='proyecto_registrar_evidencia'),
]