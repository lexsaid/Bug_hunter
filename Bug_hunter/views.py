from django.shortcuts import render

def home(request):
    return render(request, "Bug_hunter/home.html")