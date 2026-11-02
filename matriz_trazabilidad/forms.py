from django import forms
from .models import RegistroMatriz

MSG_OBLIGATORIO = "Todos los campos son obligatorios para mantener la trazabilidad"
MSG_DUPLICADO = "El identificador ya existe en este proyecto, ingrese uno único"


class BaseEslabonForm(forms.Form):
    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def id_exists(self, field_name, value):
        registros = RegistroMatriz.objects.filter(
            **{f"{field_name}__iexact": value}
        )
        if self.project is not None:
            registros = registros.filter(project=self.project)
        return registros.exists()

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in list(cleaned_data.items()):
            if isinstance(value, str):
                cleaned_data[field_name] = value.strip()
                if not cleaned_data[field_name]:
                    self.add_error(field_name, MSG_OBLIGATORIO)
        return cleaned_data


# CU-03: Registrar Requerimiento de Negocio (RN)
class RNForm(BaseEslabonForm):
    id_rn = forms.CharField(
        label="ID-RN",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. RN-01', 'class': 'input-matriz'})
    )

    def clean_id_rn(self):
        val = self.cleaned_data.get('id_rn', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        if self.id_exists("id_rn", val):
            raise forms.ValidationError(MSG_DUPLICADO)
        return val


# CU-04: Registrar Caso de Uso (CU)
class CUForm(BaseEslabonForm):
    id_cu = forms.CharField(
        label="ID-CU",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. CU-01', 'class': 'input-matriz'})
    )
    nombre_cu = forms.CharField(
        label="Nombre",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. Crear proyecto', 'class': 'input-matriz'})
    )

    def clean_id_cu(self):
        val = self.cleaned_data.get('id_cu', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        if self.id_exists("id_cu", val):
            raise forms.ValidationError(MSG_DUPLICADO)
        return val

    def clean_nombre_cu(self):
        val = self.cleaned_data.get('nombre_cu', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        return val


# CU-05: Registrar Requerimiento Funcional (RF)
class RFForm(BaseEslabonForm):
    id_rf = forms.CharField(
        label="ID-RF",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. RF-01', 'class': 'input-matriz'})
    )

    def clean_id_rf(self):
        val = self.cleaned_data.get('id_rf', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        if self.id_exists("id_rf", val):
            raise forms.ValidationError(MSG_DUPLICADO)
        return val


# CU-06: Registrar Requerimiento No Funcional (RNF)
class RNFForm(BaseEslabonForm):
    id_rnf = forms.CharField(
        label="ID-RNF",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. RNF-01', 'class': 'input-matriz'})
    )

    def clean_id_rnf(self):
        val = self.cleaned_data.get('id_rnf', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        if self.id_exists("id_rnf", val):
            raise forms.ValidationError(MSG_DUPLICADO)
        return val


# CU-07: Vincular Módulo de Desarrollo
class ModuloForm(BaseEslabonForm):
    id_modulo = forms.CharField(
        label="ID-Módulo",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. MOD-01 / views.py', 'class': 'input-matriz'})
    )

    def clean_id_modulo(self):
        val = self.cleaned_data.get('id_modulo', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        return val


# CU-08: Vincular Pantalla de Vista
class PantallaForm(BaseEslabonForm):
    id_pantalla = forms.CharField(
        label="ID-Pantalla de vista",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. PANT-01 / matriz.html', 'class': 'input-matriz'})
    )

    def clean_id_pantalla(self):
        val = self.cleaned_data.get('id_pantalla', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        return val


# CU-09: Registrar Caso de Prueba (CP)
class CPForm(BaseEslabonForm):
    id_cp = forms.CharField(
        label="ID-Caso de prueba",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. CP-01', 'class': 'input-matriz'})
    )

    def clean_id_cp(self):
        val = self.cleaned_data.get('id_cp', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        if self.id_exists("id_cp", val):
            raise forms.ValidationError(MSG_DUPLICADO)
        return val


# CU-10: Registrar Evidencia
class EvidenciaForm(BaseEslabonForm):
    evidencia = forms.CharField(
        label="URL de Evidencia",
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'https://github.com/equipo/proyecto/pull/12',
            'class': 'input-matriz'
        })
    )

    def clean_evidencia(self):
        val = self.cleaned_data.get('evidencia', '').strip()
        if not val:
            raise forms.ValidationError(MSG_OBLIGATORIO)
        return val