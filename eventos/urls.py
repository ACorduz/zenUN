from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

#Rutas de la aplicación "eventos"
urlpatterns = [
    path('eventos/', 
        views.mostrar_listaEventos, 
        name='eventos'
    ), #Vista asitirEvento
    path("asistirEvento/<int:evento_id>/",
        views.mostrar_asistirEvento,
        name='asistirEvento'
    ),
    path('generarInformes/',
        views.mostrar_vista_informes,
        name='mostrar_vista_informes'
    ), #Vista principal de informes
    path('generarInformes/informe_eventos/',
        views.procesar_informe_eventos,
        name='procesar_informe_eventos'
    ), #Procesar informe eventos
    path('generarInformes/informe_prestamos/',
        views.procesar_informe_prestamos,
        name='procesar_informe_prestamos'
    ), #Procesar informe prestamos 
    path('generarInformes/informe_asistencia/',
        views.procesar_informe_asistencia,
        name='procesar_informe_asistencia'
    ), #Procesar informe asistencia 
    path('generarInformes/descargaReportes/<str:nombreArchivoReporte>/<int:numeroReporte>/',
        views.descarga_reportes,
        name='DescargarInforme_prueba'
    ), #Descargar informe
    path('crearEvento/', 
         views.mostrar_crear_evento, 
         name='mostrar_crear_evento'
    ), #Vista para crear eventos
    path('cancelarEvento/', 
         views.mostrar_cancelar_evento, 
         name='mostrar_cancelar_evento'
    ), #Vista para crear eventos
     path('cancelarEvento/<int:evento_id>/', views.cancelar_evento, name='cancelar_evento'),
]
