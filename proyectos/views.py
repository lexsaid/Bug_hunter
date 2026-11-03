import io
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from .forms import ProjectForm, ProjectInviteForm
from .models import Project, ChecklistItem, Defect as ProjectDefect
from .permissions import accessible_projects, get_accessible_project_or_404
from checklist.models import Criterio
from matriz_trazabilidad.models import RegistroMatriz


@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            return redirect("proyectos:detalle_proyecto", project_id=project.pk)
    else:
        form = ProjectForm()
    return render(request, "sqa/create_project.html", {"form": form})


@login_required
def project_list(request):
    projects = accessible_projects(request.user)
    return render(
        request,
        "sqa/project_list.html",
        {
            "projects": projects,
            "can_create": True,
        },
    )


@login_required
def project_detail(request, project_id):
    project = get_accessible_project_or_404(request.user, project_id)
    is_owner = project.created_by_id == request.user.pk
    can_invite = is_owner
    invite_form = ProjectInviteForm(project=project) if can_invite else None

    if request.method == "POST":
        if not can_invite:
            raise PermissionDenied("Solo el Técnico QA creador puede invitar.")
        invite_form = ProjectInviteForm(request.POST, project=project)
        if invite_form.is_valid():
            membership = invite_form.save(commit=False)
            membership.project = project
            membership.invited_by = request.user
            membership.save()
            messages.success(
                request,
                f"{membership.user.username} ahora participa como Desarrollador.",
            )
            return redirect("proyectos:detalle_proyecto", project_id=project.pk)

    return render(
        request,
        "sqa/pantalla_4.html",
        {
            "project": project,
            "user_role": "Técnico QA" if is_owner else "Desarrollador",
            "can_view_checklist": is_owner,
            "can_invite": can_invite,
            "invite_form": invite_form,
            "members": project.memberships.select_related("user", "invited_by"),
        },
    )


@login_required
def view_checklist(request, project_id):
    project = get_accessible_project_or_404(request.user, project_id)
    if project.created_by_id != request.user.pk:
        raise PermissionDenied("Solo el Técnico QA del proyecto puede consultar el checklist.")
    return redirect("checklist:proyecto_lista", project_id=project_id)


def calculate_project_metrics(project):
    criteria = Criterio.objects.filter(checklist__project=project)
    total_checklist = criteria.count()
    evaluated_criteria = criteria.filter(estado__in=["cumple", "no_cumple"])
    evaluated_checklist = evaluated_criteria.count()
    completed_checklist = evaluated_criteria.filter(estado="cumple").count()
    failed_checklist = evaluated_criteria.filter(estado="no_cumple").count()

    sqa_defects = project.sqa_defects.all()
    total_sqa_defects = sqa_defects.count()
    legacy_defects = ProjectDefect.objects.filter(project=project).count()
    total_defects = total_sqa_defects + legacy_defects
    resolved_defects = sqa_defects.filter(estado="Resuelto").count()

    traceability_items = project.traceability_records.all()
    total_traceability = traceability_items.count()

    if total_checklist == 0 and total_defects == 0 and total_traceability == 0:
        return None

    complete_traceability = traceability_items.filter(
        estado=RegistroMatriz.ESTADO_COMPLETA
    ).count()
    traceability_percentage = (
        complete_traceability / total_traceability * 100
        if total_traceability > 0
        else 0
    )
    checklist_percentage = (
        completed_checklist / evaluated_checklist * 100
        if evaluated_checklist > 0
        else 0
    )
    defects_percentage = (
        resolved_defects / total_defects * 100
        if total_defects > 0
        else 100
    )

    traceability_status = _percentage_status(traceability_percentage)
    checklist_status = _percentage_status(checklist_percentage)
    defects_status = _percentage_status(defects_percentage)
    health_average = round(
        (traceability_percentage + checklist_percentage + defects_percentage) / 3,
        2,
    )
    health_status = _percentage_status(health_average)
    final_compliance = "Si cumple" if health_average >= 85 else "No cumple"

    return {
        'project': project,
        'total_checklist': total_checklist,
        'evaluated_checklist': evaluated_checklist,
        'completed_checklist': completed_checklist,
        'failed_checklist': failed_checklist,
        'checklist_percentage': round(checklist_percentage, 2),
        'checklist_status': checklist_status,
        'total_traceability': total_traceability,
        'complete_traceability': complete_traceability,
        'traceability_percentage': round(traceability_percentage, 2),
        'traceability_status': traceability_status,
        'total_defects': total_defects,
        'resolved_defects': resolved_defects,
        'defects_percentage': round(defects_percentage, 2),
        'defects_status': defects_status,
        'health_average': health_average,
        'health_status': health_status,
        'final_compliance': final_compliance,
    }


def _percentage_status(percentage):
    if percentage >= 95:
        return "Bueno"
    if percentage >= 85:
        return "Aceptable"
    return "Malo"


@login_required
def project_health_report(request, project_id):
    project = get_accessible_project_or_404(request.user, project_id)
    metrics = calculate_project_metrics(project)

    if metrics is None:
        return render(request, 'sqa/report_error.html', {
            'error_message': 'No hay datos registrados para generar el reporte',
            'project': project,
        })

    return render(request, 'sqa/health_report.html', metrics)

@login_required
def export_health_report_pdf(request, project_id):
    project = get_accessible_project_or_404(request.user, project_id)
    metrics = calculate_project_metrics(project)

    if metrics is None:
        return render(request, 'sqa/report_error.html', {
            'error_message': 'No hay datos registrados para generar el reporte',
            'project': project,
        })

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Reporte de Salud SQA - {project.name}")

    p.setFont("Helvetica", 11)
    p.drawString(100, 720, f"Periodo: {project.start_date} a {project.end_date}")
    p.drawString(100, 705, f"Creado por: {project.created_by.username}")

    p.drawString(
        100,
        670,
        f"Matriz: {metrics['traceability_percentage']}% "
        f"({metrics['complete_traceability']}/{metrics['total_traceability']} completas; "
        f"{metrics['traceability_status']})",
    )
    p.drawString(
        100,
        650,
        f"Checklist: {metrics['checklist_percentage']}% "
        f"({metrics['completed_checklist']} de {metrics['evaluated_checklist']} evaluados "
        f"cumplen; {metrics['failed_checklist']} no cumplen; {metrics['checklist_status']})",
    )
    p.drawString(
        100,
        630,
        f"Defectos resueltos: {metrics['defects_percentage']}% "
        f"({metrics['resolved_defects']}/{metrics['total_defects']}; "
        f"{metrics['defects_status']})",
    )

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 590, f"Promedio de salud: {metrics['health_average']}%")
    p.drawString(100, 570, f"Estado general: {metrics['health_status']}")
    p.drawString(100, 540, f"Dictamen Final: {metrics['final_compliance']}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Reporte_Salud_{project.name}.pdf")