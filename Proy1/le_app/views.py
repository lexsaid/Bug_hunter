from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import ProjectForm
from .models import Project, User, ChecklistItem

def qa_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == User.Role.QA_TECHNICIAN:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Solo el Técnico QA tiene permiso para realizar esta acción.")
    return wrapper

@login_required
@qa_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    
    return render(request, 'sqa/create_project.html', {'form': form})

@login_required
def view_checklist(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    checklist = project.checklist_items.all()
    
    can_edit = (request.user.role == User.Role.QA_TECHNICIAN)
    
    return render(request, 'sqa/checklist.html', {
        'project': project,
        'checklist': checklist,
        'can_edit': can_edit
    })

@login_required
def project_list(request):
    projects = Project.objects.all()
    can_create = (request.user.role == User.Role.QA_TECHNICIAN)
    
    return render(request, 'sqa/project_list.html', {
        'projects': projects,
        'can_create': can_create
    })

import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from .forms import ProjectForm
from .models import Project, User, ChecklistItem

def qa_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == User.Role.QA_TECHNICIAN:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Solo el Técnico QA tiene permiso para realizar esta acción.")
    return wrapper

@login_required
@qa_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'sqa/create_project.html', {'form': form})

@login_required
def view_checklist(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    checklist = project.checklist_items.all()
    can_edit = (request.user.role == User.Role.QA_TECHNICIAN)
    return render(request, 'sqa/checklist.html', {
        'project': project,
        'checklist': checklist,
        'can_edit': can_edit
    })

def calculate_project_metrics(project):
    total_checklist = project.checklist_items.count()
    completed_checklist = project.checklist_items.filter(is_completed=True).count()
    total_defects = project.defects.count()
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
    project = get_object_or_404(Project, id=project_id)
    metrics = calculate_project_metrics(project)

    if metrics is None:
        return render(request, 'sqa/report_error.html', {
            'error_message': 'No hay datos registrados para generar el reporte'
        })

    return render(request, 'sqa/health_report.html', metrics)

@login_required
def export_health_report_pdf(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    metrics = calculate_project_metrics(project)

    if metrics is None:
        return render(request, 'sqa/report_error.html', {
            'error_message': 'No hay datos registrados para generar el reporte'
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