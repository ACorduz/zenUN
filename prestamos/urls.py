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
            views.procesar_devolucionImplementos_mostrarInformacionPrestamo_administradorBienestar,
            name="devolucionImplementos_mostrarInformacionPrestamo"
        ) #Vista devolucionImplementos mostar la informacion del prestamo
        


]