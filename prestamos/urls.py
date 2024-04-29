from django.urls import path
from . import views

#Rutas de la aplicación "Usuarios"
urlpatterns = [
        path('solicitarPrestamo/', 
            views.mostrar_solicitarPrestamo, 
            name='solicitarPrestamo'
        ), #Vista solicitarPrestamo
        path('devolucionImplementos/', 
            views.mostrar_devolucionImplementos_administradorBienestar, 
            name='devolucionImplementos'
        ), #Vista devolucionImplementos
        path("devolucionImplementos/informacionPrestamo",
            views.mostrar_informacionPrestamo_devolucionImplementos_administradorBienestar,
            name="devolucionImplementos_mostrarInformacionPrestamo"
        ), #En la vista  devolucionImplementos mostrar la informacion del prestamo
        path("devolucionImplementos/procesarDevolucion",
            views.procesar_devolucion_devolucionImplementos_administradorBienestar,
            name="devolucionImplementos_procesarDevolucion"
        ) #En la vista  devolucionImplementos procesar devolucion implemento
]