from django.contrib import admin
from .models import User, Project, TraceabilityMatrix, Defect, ChecklistItem

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role',)

admin.site.register(Project)
admin.site.register(TraceabilityMatrix)
admin.site.register(Defect)
admin.site.register(ChecklistItem)