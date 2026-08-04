from django.urls import path
from . import views

app_name = 'Consultorias'

urlpatterns = [
    # General & Auth
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reportes-nps/', views.reportes_nps, name='reportes_nps'),
    path('reportes-nps/pdf/', views.reportes_nps_pdf, name='reportes_nps_pdf'),
    path('reportes-nps/enviar/', views.enviar_reporte_nps, name='enviar_reporte_nps'),
    path('calificar-nps/', views.calificar_nps, name='calificar_nps'),
    
    # Feature 1: FullCalendar session scheduling
    path('calendario/', views.calendario, name='calendario'),
    
    # Feature 2: jQuery UI sortable priority reordering
    path('plan-trabajo/', views.plan_trabajo, name='plan_trabajo'),
    
    # Feature 3: Hotkeys-js session note taker
    path('notas-sesion/', views.notas_sesion, name='notas_sesion'),
    path('notas-sesion/<int:sesion_id>/', views.notas_sesion, name='notas_sesion_detalle'),
    
    # Feature 4: Driver.js interactive client advance upload tour
    path('avances-cliente/', views.avances_cliente, name='avances_cliente'),

    # Entity CRUD - Consultores
    path('consultores/', views.consultores_lista, name='consultores_lista'),
    path('consultores/crear/', views.consultor_crear, name='consultor_crear'),
    path('consultores/editar/<int:pk>/', views.consultor_editar, name='consultor_editar'),
    path('consultores/eliminar/<int:pk>/', views.consultor_eliminar, name='consultor_eliminar'),

    # Entity CRUD - Clientes Mentoreados
    path('clientes/', views.clientes_lista, name='clientes_lista'),
    path('clientes/crear/', views.cliente_crear, name='cliente_crear'),
    path('clientes/editar/<int:pk>/', views.cliente_editar, name='cliente_editar'),
    path('clientes/eliminar/<int:pk>/', views.cliente_eliminar, name='cliente_eliminar'),

    # Entity CRUD - Sesiones
    path('sesiones/', views.sesiones_lista, name='sesiones_lista'),
    path('sesiones/crear/', views.sesion_crear, name='sesion_crear'),
    path('sesiones/editar/<int:pk>/', views.sesion_editar, name='sesion_editar'),
    path('sesiones/eliminar/<int:pk>/', views.sesion_eliminar, name='sesion_eliminar'),

    # Entity CRUD - Objetivos
    path('objetivos/', views.objetivos_lista, name='objetivos_lista'),
    path('objetivos/crear/', views.objetivo_crear, name='objetivo_crear'),
    path('objetivos/editar/<int:pk>/', views.objetivo_editar, name='objetivo_editar'),
    path('objetivos/eliminar/<int:pk>/', views.objetivo_eliminar, name='objetivo_eliminar'),

    # Entity CRUD - Entregables
    path('entregables/', views.entregables_lista, name='entregables_lista'),
    path('entregables/crear/', views.entregable_crear, name='entregable_crear'),
    path('entregables/editar/<int:pk>/', views.entregable_editar, name='entregable_editar'),
    path('entregables/eliminar/<int:pk>/', views.entregable_eliminar, name='entregable_eliminar'),

    # API Endpoints
    path('api/sesiones/', views.api_sesiones_eventos, name='api_sesiones_eventos'),
    path('api/sesiones/guardar/', views.api_sesion_guardar, name='api_sesion_guardar'),
    path('api/objetivos/reordenar/', views.api_objetivos_reordenar, name='api_objetivos_reordenar'),
    path('api/notas/guardar/', views.api_notas_guardar, name='api_notas_guardar'),
    path('api/entregables/subir/', views.api_entregable_subir, name='api_entregable_subir'),
]
