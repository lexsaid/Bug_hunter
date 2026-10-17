from django import forms
from .models import Defecto

class DefectoForm(forms.ModelForm):
    class Meta:
        model = Defecto
        fields = ['descripcion', 'tipo_defecto', 'proyecto_afectado', 'tecnica_sqa', 'severidad']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción breve', 'required': True}),
            'tipo_defecto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tipo de defecto', 'required': True}),
            'proyecto_afectado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Proyecto afectado', 'required': True}),
            'tecnica_sqa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Técnica SQA', 'required': True}),
            'severidad': forms.Select(attrs={'class': 'form-select'}),
        }