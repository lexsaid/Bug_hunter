from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import formset_factory
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .forms import (
    ChecklistForm,
    CriterioEdicionForm,
    CriterioForm,
    EvaluacionCriterioForm,
)
from .models import Checklist, Criterio
from proyectos.permissions import get_accessible_project_or_404


def _require_qa(user, project):
    if project is not None and project.created_by_id != user.pk:
        raise PermissionDenied("Solo el Técnico QA puede modificar checklists.")

@login_required
def lista_checklists(request, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    checklists = (
        project.checklists.all()
        if project is not None
        else Checklist.objects.filter(project__isnull=True)
    )
    return render(
        request,
        "checklist/lista_checklist.html",
        {
            "checklists": checklists,
            "project": project,
            "can_manage": project is None
            or project.created_by_id == request.user.pk,
        },
    )

@login_required
def crear_checklist(request, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    _require_qa(request.user, project)
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            checklist = form.save(commit=False)
            if project is not None:
                checklist.project = project
            checklist.save()
            if project is not None:
                return redirect(
                    "checklist:proyecto_detalle",
                    project_id=project.pk,
                    pk=checklist.pk,
                )
            return redirect("checklist:detalle", pk=checklist.pk)
    else:
        form = ChecklistForm()

    return render(
        request,
        "checklist/crear_checklist.html",
        {"form": form, "project": project},
    )

@login_required
def detalle_checklist(request, pk, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    checklist_queryset = Checklist.objects.all()
    if project is not None:
        checklist_queryset = checklist_queryset.filter(project=project)
    else:
        checklist_queryset = checklist_queryset.filter(project__isnull=True)
    checklist = get_object_or_404(checklist_queryset, pk=pk)
    criterios = list(checklist.criterios.all())
    CriterioFormSet = formset_factory(CriterioForm, extra=0)

    if request.method == "POST":
        _require_qa(request.user, project)
        formset = CriterioFormSet(request.POST)
        if formset.is_valid():
            for index, form in enumerate(formset):
                datos = form.cleaned_data
                descripcion = datos.get("descripcion")
                if not descripcion:
                    continue

                if index < len(criterios):
                    criterio = criterios[index]
                    criterio.descripcion = descripcion
                    criterio.estado = datos.get("estado", "")
                    criterio.observaciones = datos.get("observaciones", "")
                    criterio.save()
                else:
                    Criterio.objects.create(
                        checklist=checklist,
                        descripcion=descripcion,
                        estado=datos.get("estado", ""),
                        observaciones=datos.get("observaciones", ""),
                    )

            messages.success(request, "Se guardaron los criterios del checklist.")
            if project is not None:
                return redirect(
                    "checklist:proyecto_lista",
                    project_id=project.pk,
                )
            return redirect("checklist:lista")
    else:
        formset = CriterioFormSet(
            initial=[
                {
                    "descripcion": criterio.descripcion,
                    "estado": criterio.estado,
                    "observaciones": criterio.observaciones,
                }
                for criterio in criterios
            ]
        )

    return render(
        request,
        "checklist/detalle_checklist.html",
        {
            "checklist": checklist,
            "formset": formset,
            "criterios": criterios,
            "project": project,
            "can_manage": project is None
            or project.created_by_id == request.user.pk,
        },
    )

@login_required
def editar_checklist(request, pk, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    _require_qa(request.user, project)
    checklist_queryset = Checklist.objects.all()
    if project is not None:
        checklist_queryset = checklist_queryset.filter(project=project)
    else:
        checklist_queryset = checklist_queryset.filter(project__isnull=True)
    checklist = get_object_or_404(checklist_queryset, pk=pk)
    formset_class = modelformset_factory(
        Criterio,
        form=CriterioEdicionForm,
        extra=0,
        can_delete=True,
    )

    if request.method == "POST":
        form = ChecklistForm(request.POST, instance=checklist)
        formset = formset_class(
            request.POST,
            queryset=checklist.criterios.all(),
        )
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                criterios_guardados = formset.save(commit=False)
                for criterio in formset.deleted_objects:
                    criterio.delete()
                for criterio in criterios_guardados:
                    criterio.checklist = checklist
                    criterio.save()
            messages.success(request, "Se actualizó la estructura del checklist.")
            if project is not None:
                return redirect(
                    "checklist:proyecto_lista",
                    project_id=project.pk,
                )
            return redirect("checklist:lista")
    else:
        form = ChecklistForm(instance=checklist)
        formset = formset_class(queryset=checklist.criterios.all())

    return render(
        request,
        "checklist/editar_checklist.html",
        {
            "checklist": checklist,
            "form": form,
            "formset": formset,
            "project": project,
        },
    )

@login_required
def evaluar_checklist(request, pk, project_id=None):
    project = (
        get_accessible_project_or_404(request.user, project_id)
        if project_id is not None
        else None
    )
    _require_qa(request.user, project)
    checklist_queryset = Checklist.objects.all()
    if project is not None:
        checklist_queryset = checklist_queryset.filter(project=project)
    else:
        checklist_queryset = checklist_queryset.filter(project__isnull=True)
    checklist = get_object_or_404(checklist_queryset, pk=pk)
    formset_class = modelformset_factory(
        Criterio,
        form=EvaluacionCriterioForm,
        extra=0,
    )
    queryset = checklist.criterios.all()

    if request.method == "POST":
        formset = formset_class(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Se guardó la evaluación del checklist.")
            if project is not None:
                return redirect(
                    "checklist:proyecto_lista",
                    project_id=project.pk,
                )
            return redirect("checklist:lista")
    else:
        formset = formset_class(queryset=queryset)

    return render(
        request,
        "checklist/evaluar_checklist.html",
        {
            "checklist": checklist,
            "formset": formset,
            "project": project,
        },
    )
