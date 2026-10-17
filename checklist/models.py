from django.db import models


class Checklist(models.Model):
    CATEGORIAS = [
        ("documento", "Documento"),
        ("codigo", "Código"),
        ("otros", "Otros"),
    ]

    nombre = models.CharField("nombre", max_length=120)
    categoria = models.CharField("categoría", max_length=20, choices=CATEGORIAS)
    tipo_personalizado = models.CharField("tipo personalizado", max_length=60, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en", "-pk"]

    def __str__(self):
        return self.nombre

    @property
    def tipo_display(self):
        if self.categoria == "otros" and self.tipo_personalizado:
            return self.tipo_personalizado
        return self.get_categoria_display()


class Criterio(models.Model):
    ESTADOS = [
        ("cumple", "Sí cumple"),
        ("no_cumple", "No cumple"),
        ("no_aplica", "No aplica"),
    ]

    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.CASCADE,
        related_name="criterios",
    )
    descripcion = models.CharField("criterio a evaluar", max_length=250)
    estado = models.CharField(
        "cumplimiento",
        max_length=12,
        choices=ESTADOS,
        blank=True,
    )
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en", "pk"]

    def __str__(self):
        return self.descripcion
