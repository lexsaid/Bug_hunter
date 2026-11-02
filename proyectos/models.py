from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre del proyecto")
    start_date = models.DateField(verbose_name="Periodo Inicio")
    end_date = models.DateField(verbose_name="Periodo Finalización")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_invitations_sent",
    )
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_member",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.project}"


class TraceabilityMatrix(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='traceability_items')
    requirement = models.CharField(max_length=255)
    design_reference = models.CharField(max_length=255, blank=True, null=True)
    code_reference = models.CharField(max_length=255, blank=True, null=True)
    test_case_reference = models.CharField(max_length=255, blank=True, null=True)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

class Defect(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="defects",
    )
    description = models.TextField()
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class ChecklistItem(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )
    item_text = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)