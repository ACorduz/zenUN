from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
        path('eventos/', 
            views.mostrar_listaEventos, 
            name='eventos'
        ), #Vista asitirEvento
        path("asistirEvento/",
             views.mostrar_asistirevento,
             name='asistirEvento'
            ),
  path('generarInformes/',
         views.mostra_vista_informes,
         name='generarInformes') #Vista principal de informes
        ]
