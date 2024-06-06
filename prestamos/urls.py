from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

#Rutas de la aplicación "Prestamos"

urlpatterns = [
        path('solicitarPrestamo/<int:implemento_id>/', 
            views.mostrar_solicitarPrestamo, 
            name='solicitarPrestamo'
        ), #Vista solicitarPrestamo
        path('reservaExitosa/<int:implemento_id>/', 
            views.guardar_informacionPrestamo, 
            name='reservaExitosa'
        ), #Vista devolucionImplementos
        path('devolucionImplementos/', 
            views.mostrar_devolucionImplementos_administradorBienestar, 
            name='devolucionImplementos'
        ), #Vista devolucionImplementos
        path("devolucionImplementos/informacionPrestamo/",
            views.mostrar_informacionPrestamo_devolucionImplementos_administradorBienestar,
            name="devolucionImplementos_mostrarInformacionPrestamo"
        ), #En la vista  devolucionImplementos mostrar la informacion del prestamo
        path('devolucionImplementos/informacionPrestamo/<str:numeroDocumento>/', 
            views.mostrar_devolucionImplementosConParametroNumeroDocumento_administradorBienestar, 
            name='devolucionImplementosConParametroNumeroDocumento'
        ), # Vista devolucionImplementos( con paramentro CORREO en la URL) 
        path("devolucionImplementos/informacionPrestamo/<str:numeroDocumento>/procesarDevolucion/",
            views.procesar_devolucion_devolucionImplementos_administradorBienestar,
            name="devolucionImplementos_procesarDevolucion"
        ), #En la vista  devolucionImplementos( con paramentro CORREO en la URL)  procesar devolucion implemento
        ##vista Disponibilidad Implementos
        path('tablaDisponibilidadImplementos/', 
             views.mostrar_tabla_disponibilidad_implementos, 
             name='tablaDisponibilidadImplementos'),
        path("aprobarPrestamoTabla/",
            views.mostrar_tabla_aprobar,
            name="Mostrar_aprobarPrestamo_tabla"
        ),# Vista de la tabla de prestamos por aprobar por parte del administrador de bienestar
        path("procesarImplemento/<int:idImplemento>/<int:estudianteNumeroDocumento>/",
             views.procesar_implemento_AdministradorBienestar,
             name="procesarImplemento"),
        path("aprobarPrestamo/<int:idImplemento>/<int:estudianteNumeroDocumento>/<int:documento_usuario>/",
             views.procesar_aprobar_prestamo,
             name="procesarPrestamo"),
        path("llamarTareaAsincronica",
             views.generar_tareaSegundoPlano,
             name="TareaAsincronica")

]