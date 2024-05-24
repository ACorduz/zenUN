from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
        path('asistirEvento/', 
            views.mostrar_asistirEvento, 
            name='asistirEvento'
        ) #Vista asitirEvento
           
        ]