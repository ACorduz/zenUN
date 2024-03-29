from django.shortcuts import render

def registroUsuarios(request):
        return render(request, 'RegisterPage.html')
