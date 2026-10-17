from django import forms

from .models import Checklist, Criterio


class ChecklistForm(forms.ModelForm):
    ELECCION_CATEGORIA = [("", "- Selecciona una opción -")] + Checklist.CATEGORIAS

    categoria = forms.ChoiceField(
        choices=ELECCION_CATEGORIA,
        label="Tipo",
        widget=forms.Select(),
    )

    tipo_personalizado = forms.CharField(
        label="Especifica el tipo",
        max_length=60,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Escribe el tipo de checklist"}
        ),
    )

    class Meta:
        model = Checklist
        fields = ["nombre", "categoria", "tipo_personalizado"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={"placeholder": "Escribe el nombre del checklist"}
            ),
        }
        labels = {
            "nombre": "Nombre del checklist",
            "categoria": "Tipo",
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("categoria") == "otros":
            if not cleaned_data.get("tipo_personalizado", "").strip():
                self.add_error(
                    "tipo_personalizado",
                    "Escribe el tipo de checklist.",
                )
        else:
            cleaned_data["tipo_personalizado"] = ""
        return cleaned_data


class CriterioForm(forms.ModelForm):
    class Meta:
        model = Criterio
        fields = ["descripcion", "estado", "observaciones"]
        widgets = {
            "descripcion": forms.TextInput(
                attrs={"placeholder": "Escribe el criterio que se evaluará"}
            ),
            "estado": forms.Select(
                attrs={"aria-label": "Estado de cumplimiento"}
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "placeholder": "Observaciones (opcional)",
                    "rows": 2,
                }
            ),
        }
        labels = {
            "descripcion": "Criterio a evaluar",
            "estado": "Cumplimiento",
            "observaciones": "Observaciones",
        }


class CriterioEdicionForm(forms.ModelForm):
    class Meta:
        model = Criterio
        fields = ["descripcion", "estado", "observaciones"]
        widgets = {
            "descripcion": forms.TextInput(
                attrs={"placeholder": "Escribe el criterio que se evaluará"}
            ),
            "estado": forms.Select(
                attrs={"aria-label": "Estado de cumplimiento"}
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "placeholder": "Observaciones iniciales (opcional)",
                    "rows": 2,
                }
            ),
        }


class EvaluacionCriterioForm(forms.ModelForm):
    class Meta:
        model = Criterio
        fields = ["estado", "observaciones"]
        widgets = {
            "estado": forms.Select(
                attrs={"aria-label": "Estado de cumplimiento"}
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "placeholder": "Observaciones (opcional)",
                    "rows": 2,
                }
            ),
        }
