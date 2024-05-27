from django.db import models
from usuarios.models import usuario
from prestamos.models import edificio

class categoriaEvento(models.Model):
    idCategoriaEvento = models.AutoField(primary_key=True)
    nombreCategoriaEvento = models.CharField(max_length=45)
    descripcionCategoriaEvento = models.CharField(max_length=255)

class estadoEvento(models.Model):
    idEstadoEvento = models.AutoField(primary_key=True)
    nombreEstadoEvento = models.CharField(max_length=45)
    descripcionEstadoEvento = models.CharField(max_length=255)

class evento(models.Model):
    idEvento = models.AutoField(primary_key=True)
    fechaHoraCreacion = models.DateTimeField()
    numeroDocumento_AdministradorBienestar = models.ForeignKey(usuario, on_delete=models.CASCADE, related_name='NumeroDocumentoadministradorBienestar')
    nombreEvento = models.CharField(max_length=255)
    categoriaEvento_id = models.ForeignKey(categoriaEvento, on_delete=models.CASCADE)
    organizador = models.CharField(max_length=255)
    fechaHoraEvento = models.DateTimeField()
    edificio_id = models.ForeignKey(edificio, on_delete=models.CASCADE)
    lugar = models.CharField(max_length=255)
    flyer = models.BinaryField() #El tipo de dato puede cambiar
    descripcion = models.TextField()
    aforo = models.SmallIntegerField()
    asistentes = models.ManyToManyField(usuario)
    estadoEvento = models.ManyToManyField(estadoEvento)

