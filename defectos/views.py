from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Defecto
from .forms import DefectoForm

# Pantalla 8: Listar defectos (CU-07)
def lista_defectos(request):
    defectos = Defecto.objects.all().order_by('id')
    return render(request, 'defectos/pantalla8.html', {'defectos': defectos})

# Pantalla 9: Registrar defecto (CU-06)
def crear_defecto(request):
    if request.method == 'POST':
        form = DefectoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('defectos:lista')
        else:
            messages.error(request, 'Todos los campos son obligatorios.')
    else:
        form = DefectoForm()
    return render(request, 'defectos/pantalla9.html', {'form': form})

# Acción para cambiar estado a Resuelto (CU-07)
def resolver_defecto(request, defecto_id):
    defecto = get_object_or_404(Defecto, id=defecto_id)
    defecto.estado = 'Resuelto'
    defecto.save()
    return redirect('defectos:lista')