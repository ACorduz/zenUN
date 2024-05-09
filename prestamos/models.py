from django.db import models
from usuarios.models import usuario
from datetime import datetime

class edificio(models.Model):
    idEdificio = models.AutoField(primary_key=True)
    nombreEdificio = models.CharField(max_length=45)

class estadoImplemento(models.Model):
    idEstadoImplemento = models.AutoField(primary_key=True)
    nombreEstadoImplemento =  models.CharField(max_length=45)
    descripcionEstadoImplemento = models.CharField(max_length=45)

class implemento(models.Model):
    idImplemento = models.AutoField(primary_key=True)
    nombreImplemento = models.CharField(max_length=45)
    edificioId = models.ForeignKey(edificio, on_delete=models.CASCADE)
    estadoImplementoId = models.ForeignKey(estadoImplemento, on_delete=models.CASCADE)


class estadoPrestamo(models.Model):
    idEstadoPrestamo = models.AutoField(primary_key=True)
    nombreEstado = models.CharField(max_length=45)
    descripcionEstado = models.CharField(max_length=255)

class prestamo(models.Model):
    idPrestamo = models.AutoField(primary_key=True)
    estudianteNumeroDocumento = models.ForeignKey(usuario, on_delete=models.CASCADE, related_name='estudianteNumeroDocumento')
    administradorBienestarNumeroDocumento = models.ForeignKey(usuario, null=True, on_delete=models.CASCADE, related_name='administradorBienestarNumeroDocumento')
    fechaHoraCreacion = models.DateTimeField(default=datetime.now)
    ##dejar que sea nulo
    fechaHoraInicioPrestamo = models.DateTimeField(null=True)
    fechaHoraFinPrestamo = models.DateTimeField(null=True)
    idImplemento = models.ForeignKey(implemento, on_delete=models.CASCADE)
    estadoPrestamo = models.ForeignKey(estadoPrestamo, on_delete=models.CASCADE)
    comentario = models.TextField(null=True)

class comentarioImplemento(models.Model):
    idComentarioImplemento = models.AutoField(primary_key=True)
    fechaHoraCreacion = models.DateTimeField(default=datetime.now)
    comentario = models.TextField()
    implementoId = models.ForeignKey(implemento, on_delete=models.CASCADE)



