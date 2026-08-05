from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


def get_user_role(user):
    if user.is_superuser:
        return 'admin'
    if hasattr(user, 'consultor') and user.consultor:
        return 'consultor'
    if hasattr(user, 'clientementoreado') and user.clientementoreado:
        return 'cliente'
    return 'usuario'


# Modelo de Consultores
class Consultor(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    especialidad = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True, default='')
    biografia = models.TextField(blank=True, default='')
    tarifa_hora = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    estado = models.CharField(
        max_length=20,
        choices=[('ACTIVO', 'Activo'), ('INACTIVO', 'Inactivo')],
        default='ACTIVO'
    )
    fecha_registro = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Consultor'
        verbose_name_plural = 'Consultores'

    def __str__(self):
        return f"{self.nombre} - {self.especialidad}"

    # Calcular indice NPS del consultor
    def calcular_nps(self):
        sesiones = self.sesiones.filter(calificacion_nps__isnull=False)
        total = sesiones.count()
        if total == 0:
            return {'score': 0, 'promotores': 0, 'pasivos': 0, 'detractores': 0, 'total': 0, 'promedio': 0.0, 'porcentaje_promotores': 0, 'porcentaje_detractores': 0}

        promotores = sesiones.filter(calificacion_nps__gte=9).count()
        pasivos = sesiones.filter(calificacion_nps__in=[7, 8]).count()
        detractores = sesiones.filter(calificacion_nps__lte=6).count()

        pct_prom = (promotores / total) * 100
        pct_det = (detractores / total) * 100
        nps_score = round(pct_prom - pct_det, 1)
        promedio = round(sum(s.calificacion_nps for s in sesiones) / total, 1)

        return {
            'score': nps_score,
            'promotores': promotores,
            'pasivos': pasivos,
            'detractores': detractores,
            'total': total,
            'promedio': promedio,
            'porcentaje_promotores': round(pct_prom, 1),
            'porcentaje_detractores': round(pct_det, 1),
        }


# Modelo de Clientes Mentoreados
class ClienteMentoreado(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150)
    sector = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True, default='')
    consultor = models.ForeignKey(Consultor, on_delete=models.CASCADE, related_name='clientes')
    fecha_inicio = models.DateField(default=timezone.now)
    estado = models.CharField(
        max_length=20,
        choices=[('ACTIVO', 'Activo'), ('PAUSADO', 'Pausado'), ('FINALIZADO', 'Finalizado')],
        default='ACTIVO'
    )

    class Meta:
        verbose_name = 'Cliente Mentoreado'
        verbose_name_plural = 'Clientes Mentoreados'

    def __str__(self):
        return f"{self.nombre} ({self.empresa})"

    def porcentaje_cumplimiento_hitos(self):
        total = self.objetivos.count()
        if total == 0:
            return 0
        completados = self.objetivos.filter(estado='COMPLETADO').count()
        return int(round((completados / total) * 100))


# Modelo de Objetivos / Hitos de Negocio
class Objetivo(models.Model):
    cliente = models.ForeignKey(ClienteMentoreado, on_delete=models.CASCADE, related_name='objetivos')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    prioridad = models.PositiveIntegerField(default=1) # Se ordena con jQuery UI
    estado = models.CharField(
        max_length=20,
        choices=[('PENDIENTE', 'Pendiente'), ('EN_PROCESO', 'En Proceso'), ('COMPLETADO', 'Completado')],
        default='PENDIENTE'
    )
    fecha_limite = models.DateField(null=True, blank=True)
    progreso_porcentaje = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['prioridad', 'id']
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'

    def __str__(self):
        return f"P{self.prioridad}: {self.titulo}"


# Modelo de Entregables / Avances
class Entregable(models.Model):
    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE, related_name='entregables')
    cliente = models.ForeignKey(ClienteMentoreado, on_delete=models.CASCADE, related_name='entregables')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    archivo = models.FileField(upload_to='entregables/', null=True, blank=True)
    enlace_externo = models.URLField(blank=True, default='')
    estado = models.CharField(
        max_length=20,
        choices=[('PENDIENTE', 'Pendiente'), ('EN_REVISION', 'En Revisión'), ('APROBADO', 'Aprobado'), ('RECHAZADO', 'Rechazado')],
        default='PENDIENTE'
    )
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    comentarios_consultor = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-fecha_entrega']
        verbose_name = 'Entregable'
        verbose_name_plural = 'Entregables'

    def __str__(self):
        return self.titulo


# Modelo de Sesiones de Mentoria
class SesionMentoria(models.Model):
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(
        max_length=20,
        choices=[('INDIVIDUAL', 'Individual'), ('GRUPAL', 'Grupal')],
        default='INDIVIDUAL'
    )
    consultor = models.ForeignKey(Consultor, on_delete=models.CASCADE, related_name='sesiones')
    cliente = models.ForeignKey(ClienteMentoreado, on_delete=models.SET_NULL, null=True, blank=True, related_name='sesiones_individuales')
    clientes_grupales = models.ManyToManyField(ClienteMentoreado, blank=True, related_name='sesiones_grupales')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    modalidad = models.CharField(
        max_length=20,
        choices=[('VIRTUAL', 'Virtual'), ('PRESENCIAL', 'Presencial')],
        default='VIRTUAL'
    )
    enlace_reunion = models.URLField(blank=True, default='')
    estado = models.CharField(
        max_length=20,
        choices=[('PROGRAMADA', 'Programada'), ('COMPLETADA', 'Completada'), ('CANCELADA', 'Cancelada')],
        default='PROGRAMADA'
    )
    notas_sesion = models.TextField(blank=True, default='')
    calificacion_nps = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    feedback_cliente = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = 'Sesión de Mentoría'
        verbose_name_plural = 'Sesiones de Mentoría'

    def __str__(self):
        return f"{self.titulo} - {self.consultor.nombre}"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.titulo,
            'start': self.fecha_inicio.isoformat(),
            'end': self.fecha_fin.isoformat(),
            'tipo': self.tipo,
            'consultor_id': self.consultor.id,
            'consultor_nombre': self.nombre_consultor(),
            'cliente_id': self.cliente.id if self.cliente else None,
            'modalidad': self.modalidad,
            'estado': self.estado,
            'notas_sesion': self.notas_sesion,
            'backgroundColor': '#5fcf80' if self.tipo == 'INDIVIDUAL' else '#007bff',
            'borderColor': '#3cb371' if self.tipo == 'INDIVIDUAL' else '#0056b3',
        }

    def nombre_consultor(self):
        return self.consultor.nombre
