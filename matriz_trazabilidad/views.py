from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import RegistroMatriz
from proyectos.permissions import get_accessible_project_or_404
from .forms import (
    RNForm, CUForm, RFForm, RNFForm,
    ModuloForm, PantallaForm, CPForm, EvidenciaForm
)


def _get_project(request, project_id):
    if project_id is None:
        return None
    return get_accessible_project_or_404(request.user, project_id)


def _get_record(pk, project):
    registros = RegistroMatriz.objects.all()
    if project is None:
        registros = registros.filter(project__isnull=True)
    else:
        registros = registros.filter(project=project)
    return get_object_or_404(registros, pk=pk)


def _matrix_url_name(project, global_name, project_name):
    return (
        f"matriz_trazabilidad:{project_name}"
        if project is not None
        else f"matriz_trazabilidad:{global_name}"
    )


def _redirect_to_matrix(project):
    if project is not None:
        return redirect(
            "matriz_trazabilidad:proyecto_lista",
            project_id=project.pk,
        )
    return redirect("matriz_trazabilidad:vista_matriz")


@login_required
def vista_matriz(request, project_id=None):
    """Muestra la tabla principal de la Matriz de Trazabilidad y métricas de completitud."""
    project = _get_project(request, project_id)
    registros = RegistroMatriz.objects.all()
    if project is None:
        registros = registros.filter(project__isnull=True)
    else:
        registros = registros.filter(project=project)
    total = registros.count()
    completas = registros.filter(estado=RegistroMatriz.ESTADO_COMPLETA).count()
    parciales = total - completas
    porcentaje_completitud = round((completas / total) * 100, 2) if total > 0 else 0

    context = {
        'registros': registros,
        'project': project,
        'total': total,
        'completas': completas,
        'parciales': parciales,
        'porcentaje_completitud': porcentaje_completitud,
    }
    return render(request, 'matriz_trazabilidad/matriz.html', context)


# CU-03: Registrar Requerimiento de Negocio (RN)
@login_required
def registrar_rn(request, project_id=None):
    project = _get_project(request, project_id)
    if request.method == 'POST':
        form = RNForm(request.POST, project=project)
        if form.is_valid():
            RegistroMatriz.objects.create(
                id_rn=form.cleaned_data['id_rn'],
                project=project,
            )
            return _redirect_to_matrix(project)
    else:
        form = RNForm(project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-03: Agregar Requerimiento de Negocio (RN)',
        'texto_boton': 'Guardar',
        'contexto_padre': None,
        'project': project,
        'cancel_url_name': _matrix_url_name(
            project,
            "vista_matriz",
            "proyecto_lista",
        ),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })


# CU-04: Registrar Caso de Uso (CU) — Soporta 1:N desde un RN
@login_required
def registrar_cu(request, pk, project_id=None):
    project = _get_project(request, project_id)
    fila_base = _get_record(pk, project)

    if request.method == 'POST':
        form = CUForm(request.POST, project=project)
        if form.is_valid():
            # Si la fila base aún no tiene CU asignado, se actualiza; si ya tiene, se crea nueva fila 1:N
            if not fila_base.id_cu:
                fila_base.id_cu = form.cleaned_data['id_cu']
                fila_base.nombre_cu = form.cleaned_data['nombre_cu']
                fila_base.save()
            else:
                RegistroMatriz.objects.create(
                    id_rn=fila_base.id_rn,
                    id_cu=form.cleaned_data['id_cu'],
                    nombre_cu=form.cleaned_data['nombre_cu'],
                    project=project,
                )
            return _redirect_to_matrix(project)
    else:
        form = CUForm(project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-04: Agregar Caso de Uso (CU)',
        'texto_boton': 'Guardar CU',
        'contexto_padre': f"Vinculado a ID-RN: {fila_base.id_rn}",
        'project': project,
        'cancel_url_name': _matrix_url_name(project, "vista_matriz", "proyecto_lista"),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })


# CU-05: Registrar Requerimiento Funcional (RF) — Soporta 1:N desde un CU
@login_required
def registrar_rf(request, pk, project_id=None):
    project = _get_project(request, project_id)
    fila_base = _get_record(pk, project)
    if not fila_base.id_cu:
        return _redirect_to_matrix(project)

    if request.method == 'POST':
        form = RFForm(request.POST, project=project)
        if form.is_valid():
            if not fila_base.id_rf:
                fila_base.id_rf = form.cleaned_data['id_rf']
                fila_base.save()
            else:
                RegistroMatriz.objects.create(
                    id_rn=fila_base.id_rn,
                    id_cu=fila_base.id_cu,
                    nombre_cu=fila_base.nombre_cu,
                    id_rf=form.cleaned_data['id_rf'],
                    project=project,
                )
            return _redirect_to_matrix(project)
    else:
        form = RFForm(project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-05: Agregar Requerimiento Funcional (RF) asociado',
        'texto_boton': 'Guardar RF',
        'contexto_padre': f"Vinculado a: {fila_base.id_rn} ➔ {fila_base.id_cu} ({fila_base.nombre_cu})",
        'project': project,
        'cancel_url_name': _matrix_url_name(project, "vista_matriz", "proyecto_lista"),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })


# CU-06: Registrar Requerimiento No Funcional (RNF) — Soporta 1:N desde un RF
@login_required
def registrar_rnf(request, pk, project_id=None):
    project = _get_project(request, project_id)
    fila_base = _get_record(pk, project)
    if not fila_base.id_rf:
        return _redirect_to_matrix(project)

    if request.method == 'POST':
        form = RNFForm(request.POST, project=project)
        if form.is_valid():
            if not fila_base.id_rnf:
                fila_base.id_rnf = form.cleaned_data['id_rnf']
                fila_base.save()
            else:
                RegistroMatriz.objects.create(
                    id_rn=fila_base.id_rn,
                    id_cu=fila_base.id_cu,
                    nombre_cu=fila_base.nombre_cu,
                    id_rf=fila_base.id_rf,
                    id_rnf=form.cleaned_data['id_rnf'],
                    project=project,
                )
            return _redirect_to_matrix(project)
    else:
        form = RNFForm(project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-06: Agregar Requerimiento No Funcional (RNF)',
        'texto_boton': 'Guardar RNF',
        'contexto_padre': f"Vinculado a: {fila_base.id_rn} ➔ {fila_base.id_cu} ➔ {fila_base.id_rf}",
        'project': project,
        'cancel_url_name': _matrix_url_name(project, "vista_matriz", "proyecto_lista"),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })


# CU-07: Vincular Módulo de Desarrollo — Soporta 1:N desde un RNF
@login_required
def vincular_modulo(request, pk, project_id=None):
    project = _get_project(request, project_id)
    fila_base = _get_record(pk, project)
    if not fila_base.id_rnf:
        return _redirect_to_matrix(project)

    if request.method == 'POST':
        form = ModuloForm(request.POST, project=project)
        if form.is_valid():
            if not fila_base.id_modulo:
                fila_base.id_modulo = form.cleaned_data['id_modulo']
                fila_base.save()
            else:
                RegistroMatriz.objects.create(
                    id_rn=fila_base.id_rn,
                    id_cu=fila_base.id_cu,
                    nombre_cu=fila_base.nombre_cu,
                    id_rf=fila_base.id_rf,
                    id_rnf=fila_base.id_rnf,
                    id_modulo=form.cleaned_data['id_modulo'],
                    project=project,
                )
            return _redirect_to_matrix(project)
    else:
        form = ModuloForm(project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-07: Vincular Módulo de desarrollo',
        'texto_boton': 'Guardar Módulo',
        'contexto_padre': f"Vinculado a: {fila_base.id_rf} / {fila_base.id_rnf}",
        'project': project,
        'cancel_url_name': _matrix_url_name(project, "vista_matriz", "proyecto_lista"),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })


# CU-08: Vincular Pantalla de Vista — Soporta 1:N desde un Módulo
@login_required
def vincular_pantalla(request, pk, project_id=None):
    project = _get_project(request, project_id)
    fila_base = _get_record(pk, project)
    if not fila_base.id_modulo:
        return _redirect_to_matrix(project)

    if request.method == 'POST':
        form = PantallaForm(request.POST, project=project)
        if form.is_valid():
            if not fila_base.id_pantalla:
                fila_base.id_pantalla = form.cleaned_data['id_pantalla']
                fila_base.save()
            else:
                RegistroMatriz.objects.create(
                    id_rn=fila_base.id_rn,
                    id_cu=fila_base.id_cu,
                    nombre_cu=fila_base.nombre_cu,
                    id_rf=fila_base.id_rf,
                    id_rnf=fila_base.id_rnf,
                    id_modulo=fila_base.id_modulo,
                    id_pantalla=form.cleaned_data['id_pantalla'],
                    project=project,
                )
            return _redirect_to_matrix(project)
    else:
        form = PantallaForm(project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-08: Vincular Pantalla de vista',
        'texto_boton': 'Guardar Pantalla',
        'contexto_padre': f"Vinculado a Módulo: {fila_base.id_modulo}",
        'project': project,
        'cancel_url_name': _matrix_url_name(project, "vista_matriz", "proyecto_lista"),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })


# CU-09: Registrar Caso de Prueba (CP) — Soporta 1:N desde Módulo y Pantalla
@login_required
def registrar_cp(request, pk, project_id=None):
    project = _get_project(request, project_id)
    fila_base = _get_record(pk, project)
    if not (fila_base.id_modulo and fila_base.id_pantalla):
        return _redirect_to_matrix(project)

    if request.method == 'POST':
        form = CPForm(request.POST, project=project)
        if form.is_valid():
            if not fila_base.id_cp:
                fila_base.id_cp = form.cleaned_data['id_cp']
                fila_base.save()
            else:
                RegistroMatriz.objects.create(
                    id_rn=fila_base.id_rn,
                    id_cu=fila_base.id_cu,
                    nombre_cu=fila_base.nombre_cu,
                    id_rf=fila_base.id_rf,
                    id_rnf=fila_base.id_rnf,
                    id_modulo=fila_base.id_modulo,
                    id_pantalla=fila_base.id_pantalla,
                    id_cp=form.cleaned_data['id_cp'],
                    project=project,
                )
            return _redirect_to_matrix(project)
    else:
        form = CPForm(project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-09: Vincular Caso de Prueba (CP)',
        'texto_boton': 'Guardar Caso de Prueba',
        'contexto_padre': f"Vinculado a: {fila_base.id_rf} | {fila_base.id_modulo} | {fila_base.id_pantalla}",
        'project': project,
        'cancel_url_name': _matrix_url_name(project, "vista_matriz", "proyecto_lista"),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })


# CU-10: Registrar Evidencia (Cierra el ciclo y pasa la fila a "Completa")
@login_required
def registrar_evidencia(request, pk, project_id=None):
    project = _get_project(request, project_id)
    fila_base = _get_record(pk, project)
    if not fila_base.id_cp:
        return _redirect_to_matrix(project)

    if request.method == 'POST':
        form = EvidenciaForm(request.POST, project=project)
        if form.is_valid():
            fila_base.evidencia = form.cleaned_data['evidencia']
            fila_base.save()  # Cambia automáticamente a "Completa" al tener los 8 eslabones
            return _redirect_to_matrix(project)
    else:
        form = EvidenciaForm(initial={'evidencia': fila_base.evidencia}, project=project)

    return render(request, 'matriz_trazabilidad/formulario_eslabon.html', {
        'form': form,
        'titulo_cu': 'CU-10: Agregar Evidencia',
        'texto_boton': 'Guardar Evidencia',
        'contexto_padre': f"Cerrando trazabilidad del Caso de Prueba: {fila_base.id_cp}",
        'project': project,
        'cancel_url_name': _matrix_url_name(project, "vista_matriz", "proyecto_lista"),
        'cancel_url_kwargs': {"project_id": project.pk} if project else {},
    })