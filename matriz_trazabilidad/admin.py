from django.contrib import admin

from .models import RegistroMatriz


@admin.register(RegistroMatriz)
class RegistroMatrizAdmin(admin.ModelAdmin):
    list_display = (
        "id_rn",
        "id_cu",
        "id_rf",
        "id_rnf",
        "id_cp",
        "estado",
        "project",
    )
    list_filter = ("estado", "project")
    search_fields = ("id_rn", "id_cu", "id_rf", "id_rnf", "id_cp")
