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
            "can_invite": can_invite,
            "invite_form": invite_form,
            "members": project.memberships.select_related("user", "invited_by"),
        },
    )


@login_required
def view_checklist(request, project_id):
    get_accessible_project_or_404(request.user, project_id)
    return redirect("checklist:proyecto_lista", project_id=project_id)


def calculate_project_metrics(project):
    criteria = Criterio.objects.filter(checklist__project=project)
    total_checklist = criteria.count()
    completed_checklist = criteria.exclude(estado="").count()
    total_defects = project.sqa_defects.count() + ProjectDefect.objects.filter(
        project=project
    ).count()
    traceability_items = project.traceability_items.all()
    total_traceability = traceability_items.count()

    if total_checklist == 0 and total_defects == 0 and total_traceability == 0:
        return None

    weighted_traceability_score = 0
    for item in traceability_items:
        has_design_or_code = bool(item.design_reference or item.code_reference)
        has_test = bool(item.test_case_reference)
        if has_design_or_code and has_test:
            weighted_traceability_score += 100
        elif has_design_or_code:
            weighted_traceability_score += 50

    traceability_percentage = (weighted_traceability_score / total_traceability) if total_traceability > 0 else 0

    if traceability_percentage > 95:
        traceability_status = "Bueno"
    elif 85 <= traceability_percentage <= 94:
        traceability_status = "Aceptable"
    else:
        traceability_status = "Malo"

    checklist_percentage = (completed_checklist / total_checklist * 100) if total_checklist > 0 else 0
    if checklist_percentage >= 95:
        checklist_status = "Bueno"
    elif 90 <= checklist_percentage < 95:
        checklist_status = "Aceptable"
    else:
        checklist_status = "Malo"

    acceptable_or_better_count = sum([
        1 for status in [traceability_status, checklist_status] if status in ["Bueno", "Aceptable"]
    ])
    
    final_compliance = "Si cumple" if acceptable_or_better_count >= 2 else "No cumple"

    return {
        'project': project,
        'total_checklist': total_checklist,
        'completed_checklist': completed_checklist,
        'checklist_percentage': round(checklist_percentage, 2),
        'checklist_status': checklist_status,
        'total_traceability': total_traceability,
        'traceability_percentage': round(traceability_percentage, 2),
        'traceability_status': traceability_status,
        'total_defects': total_defects,
        'final_compliance': final_compliance,
    }

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

    p.drawString(100, 670, f"Trazabilidad: {metrics['traceability_percentage']}% ({metrics['traceability_status']})")
    p.drawString(100, 650, f"Checklist Completado: {metrics['checklist_percentage']}% ({metrics['checklist_status']})")
    p.drawString(100, 630, f"Total de Defectos: {metrics['total_defects']}")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 580, f"Dictamen Final: {metrics['final_compliance']}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Reporte_Salud_{project.name}.pdf")