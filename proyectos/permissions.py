from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Project


def accessible_projects(user):
    projects = Project.objects.all()
    if user.is_superuser:
        return projects
    return projects.filter(
        Q(created_by=user) | Q(memberships__user=user)
    ).distinct()


def get_accessible_project_or_404(user, project_id):
    return get_object_or_404(accessible_projects(user), pk=project_id)
