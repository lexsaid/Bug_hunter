from django import forms
from django.contrib.auth import get_user_model

from .models import Project, ProjectMember

Usuario = get_user_model()

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto para nombre del proyecto'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ProjectInviteForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ["user"]
        labels = {"user": "Desarrollador"}
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        invited_ids = project.memberships.values_list("user_id", flat=True)
        self.fields["user"].queryset = Usuario.objects.filter(
            is_active=True,
        ).exclude(pk=project.created_by_id).exclude(pk__in=invited_ids)