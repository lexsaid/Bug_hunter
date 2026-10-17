from django.contrib import admin

from .models import Checklist, Criterio


class CriterioInline(admin.TabularInline):
    model = Criterio
    extra = 0


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "creado_en")
    inlines = [CriterioInline]


@admin.register(Criterio)
class CriterioAdmin(admin.ModelAdmin):
    list_display = ("descripcion", "checklist", "estado")
    list_filter = ("estado", "checklist")
