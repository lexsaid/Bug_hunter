# seccion usuarios

from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username