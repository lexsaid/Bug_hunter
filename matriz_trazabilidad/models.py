from django.db import models


class RegistroMatriz(models.Model):
    ESTADO_PARCIAL = 'Parcial'
    ESTADO_COMPLETA = 'Completa'

    ESTADOS_CHOICES = [
        (ESTADO_PARCIAL, 'Parcial'),
        (ESTADO_COMPLETA, 'Completa'),
    ]

    id_rn = models.CharField("ID-RN", max_length=50)
    id_cu = models.CharField("ID-CU", max_length=50, blank=True, default="")
    nombre_cu = models.CharField("Nombre", max_length=150, blank=True, default="")
    id_rf = models.CharField("ID-RF", max_length=50, blank=True, default="")
    id_rnf = models.CharField("ID-RNF", max_length=50, blank=True, default="")
    id_modulo = models.CharField("ID-Módulo", max_length=100, blank=True, default="")
    id_pantalla = models.CharField("ID-Pantalla de vista", max_length=100, blank=True, default="")
    id_cp = models.CharField("ID-Caso de prueba", max_length=50, blank=True, default="")
    evidencia = models.URLField("URL de Evidencia", max_length=500, blank=True, default="")
    estado = models.CharField("Estado", max_length=20, choices=ESTADOS_CHOICES, default=ESTADO_PARCIAL)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        "proyectos.Project",
        on_delete=models.CASCADE,
        related_name="traceability_records",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['id_rn', 'id_cu', 'id_rf', 'id_rnf', 'id_cp', 'id']
        verbose_name = "Registro de Matriz de Trazabilidad"
        verbose_name_plural = "Registros de Matriz de Trazabilidad"

    def verificar_completitud(self):
        """Verifica si todos los eslabones (CU-03 a CU-10) están presentes."""
        eslabones = [
            self.id_rn,
            self.id_cu,
            self.nombre_cu,
            self.id_rf,
            self.id_rnf,
            self.id_modulo,
            self.id_pantalla,
            self.id_cp,
            self.evidencia,
        ]
        return all(bool(str(valor).strip()) for valor in eslabones)

    def save(self, *args, **kwargs):
        if self.verificar_completitud():
            self.estado = self.ESTADO_COMPLETA
        else:
            self.estado = self.ESTADO_PARCIAL
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_rn} | {self.id_cu or '-'} | {self.id_rf or '-'} ({self.estado})"