from django.contrib import admin

from .models import Defecto


@admin.register(Defecto)
class DefectoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descripcion", "project", "severidad", "estado")
    list_filter = ("severidad", "estado")
    search_fields = ("codigo", "descripcion", "proyecto_afectado")
