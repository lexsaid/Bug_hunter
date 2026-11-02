from django.contrib import admin

from .models import ChecklistItem, Defect, Project, ProjectMember, TraceabilityMatrix


admin.site.register(Project)
admin.site.register(ProjectMember)
admin.site.register(TraceabilityMatrix)
admin.site.register(Defect)
admin.site.register(ChecklistItem)
