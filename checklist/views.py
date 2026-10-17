from django.contrib import messages
from django.forms import formset_factory
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ChecklistForm,
    CriterioEdicionForm,
    CriterioForm,
    EvaluacionCriterioForm,
)
from .models import Checklist, Criterio


def lista_checklists(request):
    return render(
        request,
        "checklist/lista_checklist.html",
        {
            "checklists": Checklist.objects.all(),
        },
    )


def crear_checklist(request):
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            checklist = form.save()
            return redirect("checklist:detalle", pk=checklist.pk)
    else:
        form = ChecklistForm()

    return render(
        request,
        "checklist/crear_checklist.html",
        {"form": form},
    )


def detalle_checklist(request, pk):
    checklist = get_object_or_404(Checklist, pk=pk)
    criterios = list(checklist.criterios.all())
    CriterioFormSet = formset_factory(CriterioForm, extra=0)

    if request.method == "POST":
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
        },
    )


def editar_checklist(request, pk):
    checklist = get_object_or_404(Checklist, pk=pk)
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
            form.save()
            formset.save()
            messages.success(request, "Se actualizó la estructura del checklist.")
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
        },
    )


def evaluar_checklist(request, pk):
    checklist = get_object_or_404(Checklist, pk=pk)
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
            return redirect("checklist:lista")
    else:
        formset = formset_class(queryset=queryset)

    return render(
        request,
        "checklist/evaluar_checklist.html",
        {
            "checklist": checklist,
            "formset": formset,
        },
    )
