from django.db import models

class Defecto(models.Model):
    SEVERIDAD_CHOICES = [
        ('Crítico', 'Crítico'),
        ('Menor', 'Menor'),
    ]

    ESTADO_CHOICES = [
        ('Abierto', 'Abierto'),
        ('Resuelto', 'Resuelto'),
    ]

    # Identificador autogenerado (ej. DEF-001) para cumplir el RNF
    codigo = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    descripcion = models.CharField(max_length=255)
    tipo_defecto = models.CharField(max_length=100)
    proyecto_afectado = models.CharField(max_length=100)
    tecnica_sqa = models.CharField(max_length=100)
    severidad = models.CharField(max_length=10, choices=SEVERIDAD_CHOICES, default='Menor')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Abierto')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Defecto.objects.all().order_by('id').last()
            nuevo_num = 1 if not ultimo else ultimo.id + 1
            self.codigo = f"DEF-{nuevo_num:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"