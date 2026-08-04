from django.contrib import admin
from .models import Consultor, ClienteMentoreado, Objetivo, Entregable, SesionMentoria


@admin.register(Consultor)
class ConsultorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'email', 'telefono', 'tarifa_hora', 'estado', 'fecha_registro')
    list_filter = ('estado', 'especialidad')
    search_fields = ('nombre', 'email', 'especialidad')


@admin.register(ClienteMentoreado)
class ClienteMentoreadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'sector', 'email', 'consultor', 'estado', 'fecha_inicio')
    list_filter = ('estado', 'sector', 'consultor')
    search_fields = ('nombre', 'empresa', 'email')


@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cliente', 'prioridad', 'estado', 'progreso_porcentaje', 'fecha_limite')
    list_filter = ('estado', 'cliente')
    search_fields = ('titulo', 'cliente__nombre', 'cliente__empresa')
    ordering = ('cliente', 'prioridad')


@admin.register(Entregable)
class EntregableAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cliente', 'objetivo', 'estado', 'fecha_entrega')
    list_filter = ('estado', 'cliente')
    search_fields = ('titulo', 'cliente__nombre')


@admin.register(SesionMentoria)
class SesionMentoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'consultor', 'cliente', 'fecha_inicio', 'modalidad', 'estado', 'calificacion_nps')
    list_filter = ('tipo', 'modalidad', 'estado', 'consultor')
    search_fields = ('titulo', 'consultor__nombre', 'cliente__nombre')
