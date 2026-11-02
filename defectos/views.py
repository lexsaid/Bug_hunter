from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Defecto
from .forms import DefectoForm
from django.contrib.auth.decorators import login_required
from proyectos.permissions import get_accessible_project_or_404

# Pantalla 8: Listar defectos (CU-07)
@login_required
def lista_defectos(request, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    defectos = Defecto.objects.all()
    if project is not None:
        defectos = defectos.filter(project=project)
    else:
        defectos = defectos.filter(project__isnull=True)
    return render(
        request,
        "defectos/pantalla8.html",
        {"defectos": defectos.order_by("id"), "project": project},
    )

# Pantalla 9: Registrar defecto (CU-06)
@login_required 
def crear_defecto(request, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    if request.method == 'POST':
        form = DefectoForm(request.POST, project=project)
        if form.is_valid():
            defecto = form.save(commit=False)
            if project is not None:
                defecto.project = project
                defecto.proyecto_afectado = project.name
            defecto.save()
            if project is not None:
                return redirect(
                    "defectos:proyecto_lista",
                    project_id=project.pk,
                )
            return redirect('defectos:lista')
        else:
            messages.error(request, 'Todos los campos son obligatorios.')
    else:
        form = DefectoForm(project=project)
    return render(
        request,
        "defectos/pantalla9.html",
        {"form": form, "project": project},
    )

# Acción para cambiar estado a Resuelto (CU-07)
@login_required
def resolver_defecto(request, defecto_id, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    queryset = Defecto.objects.all()
    if project is not None:
        queryset = queryset.filter(project=project)
    else:
        queryset = queryset.filter(project__isnull=True)
    defecto = get_object_or_404(queryset, id=defecto_id)
    defecto.estado = 'Resuelto'
    defecto.save()
    if project is not None:
        return redirect("defectos:proyecto_lista", project_id=project.pk)
    return redirect('defectos:lista')