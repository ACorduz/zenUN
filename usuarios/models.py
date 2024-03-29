from django.db import models

#Modelo para la entidad Tipo de documento
class tipoDocumento(models.Model):
    idTipoDocumento = models.AutoField(primary_key=True)
    siglasTipoDocumento = models.CharField(max_length=5)
    descripcionTipoDocumento = models.CharField(max_length=45)

#Modelo para la entidad Rol
class rol(models.Model):
    idRol = models.AutoField(primary_key=True)
    nombreRol = models.CharField(max_length=45)
    descripcionRol = models.CharField(max_length=255)

#Modelo para la entidad usuario
class usuario(models.Model):
    numeroDocumento = models.IntegerField(primary_key=True)
    idTipoDocumento = models.ForeignKey(tipoDocumento, on_delete=models.CASCADE) #llave foránea
    nombres = models.CharField(max_length=45)
    apellidos = models.CharField(max_length=45)
    correoInstitucional = models.CharField(max_length=50, unique=True) #UNIQUE para que no se pueda repetir el correo.
    numeroCelular = models.CharField(max_length=15)
    roles = models.ManyToManyField(rol) #Crea la relación muchos a muchos
    codigoVerificacion = models.IntegerField() #Campo INT para el proceso de verificación de correo
    usuarioVerificado = models.BooleanField(default=False) #Si es TRUE el usuario ha sido verificado


