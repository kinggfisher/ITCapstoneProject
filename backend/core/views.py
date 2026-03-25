from django.http import JsonResponse
from django.shortcuts import render

def home(request):
    return JsonResponse({"message": "Welcome to the IT Capstone Project API"})

def demo(request):
    return render(request, 'demo.html')