from django.db import models
from usuarios.models import usuario
from prestamos.models import edificio
from usuarios.models import razonCambio
from simple_history.models import HistoricalRecords
from datetime import datetime, timedelta

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
    fechaHoraEventoFinal = models.DateTimeField(default=datetime.now() + timedelta(hours=1))  # Nuevo campo con valor predeterminado
    edificio_id = models.ForeignKey(edificio, on_delete=models.CASCADE)
    lugar = models.CharField(max_length=255)
    flyer = models.BinaryField() #El tipo de dato puede cambiar
    descripcion = models.TextField()
    aforo = models.SmallIntegerField()
    asistentes = models.ManyToManyField(usuario)
    estadoEvento = models.ManyToManyField(estadoEvento)
    history = HistoricalRecords(excluded_fields=['flyer'],history_change_reason_field=models.ForeignKey(razonCambio, null=True, on_delete=models.CASCADE),m2m_fields=[asistentes, estadoEvento],table_name = 'trazabilidadEventos',cascade_delete_history=True)           

class tipoInforme(models.Model):
    idTipoInforme = models.AutoField(primary_key=True)
    tipo_informe = models.CharField(max_length=255)
class trazabilidadInformes(models.Model):
    idInforme = models.AutoField(primary_key=True)
    fechaGeneracionInforme = models.DateTimeField()
    tipoInforme = models.ForeignKey(tipoInforme, on_delete=models.CASCADE)