from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth import logout
from usuarios.models import Usuario

@login_required
def home(request):
    return render(request, "Bug_hunter/home.html")


def login(request):
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        usuario = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if usuario is not None:
            auth_login(request, usuario)
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("proyectos:lista_proyectos")
        return render(
            request,
            "Bug_hunter/login.html",
            {
                "error": "Nombre de usuario o contraseña incorrectos.",
                "next": next_url,
            },
        )

    return render(
        request,
        "Bug_hunter/login.html",
        {"next": next_url},
    )

def registrar_usuario_normal(request):
    if request.method == "POST":
        nombre_usuario = request.POST.get("username")
        correo = request.POST.get("email")
        password = request.POST.get("password")

        # La contraseña se cifra mediante create_user.
        usuario = Usuario.objects.create_user(
            username=nombre_usuario,
            email=correo,
            password=password
        )
        return redirect("login")

    return render(request, "usuarios/registro.html")

def cerrar_sesion(request):
    logout(request)
    return redirect('login')
