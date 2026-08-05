from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.db.models import Q
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.views.decorators.http import require_POST
from django.utils import timezone
from xhtml2pdf import pisa
import base64
import io
import json
import logging
import qrcode

from .models import Consultor, ClienteMentoreado, Objetivo, Entregable, SesionMentoria, get_user_role


logger = logging.getLogger(__name__)


# --- INICIO Y AUTENTICACION ---

def index(request):
    consultores = Consultor.objects.filter(estado='ACTIVO')
    stats = {
        'total_consultores': Consultor.objects.count(),
        'total_clientes': ClienteMentoreado.objects.count(),
        'total_sesiones': SesionMentoria.objects.count(),
        'total_objetivos': Objetivo.objects.count(),
    }
    return render(request, 'index.html', {'consultores': consultores, 'stats': stats})


def logout_view(request):
    auth_logout(request)
    return redirect('Consultorias:index')


# --- DASHBOARD Y REPORTES ---

@login_required
def dashboard(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        cliente = request.user.clientementoreado
        clientes = ClienteMentoreado.objects.filter(id=cliente.id)
    elif role == 'consultor':
        consultor = request.user.consultor
        clientes = consultor.clientes.all()
    else:
        clientes = ClienteMentoreado.objects.all()

    total_clientes = clientes.count()
    objetivos = Objetivo.objects.filter(cliente__in=clientes)
    total_objetivos = objetivos.count()
    completados = objetivos.filter(estado='COMPLETADO').count()
    en_proceso = objetivos.filter(estado='EN_PROCESO').count()
    pendientes = objetivos.filter(estado='PENDIENTE').count()

    clientes_progreso = []
    for c in clientes:
        tot_h = c.objetivos.count()
        comp_h = c.objetivos.filter(estado='COMPLETADO').count()
        proc_h = c.objetivos.filter(estado='EN_PROCESO').count()
        pend_h = c.objetivos.filter(estado='PENDIENTE').count()
        pct = c.porcentaje_cumplimiento_hitos()
        clientes_progreso.append({
            'cliente': c,
            'total_hitos': tot_h,
            'completados': comp_h,
            'en_proceso': proc_h,
            'pendientes': pend_h,
            'porcentaje': pct
        })

    tasa_cumplimiento = 0
    if total_objetivos > 0:
        tasa_cumplimiento = int(round((completados / total_objetivos) * 100))

    return render(request, 'dashboard.html', {
        'total_clientes': total_clientes,
        'total_objetivos': total_objetivos,
        'objetivos_completados': completados,
        'objetivos_en_proceso': en_proceso,
        'objetivos_pendientes': pendientes,
        'tasa_cumplimiento': tasa_cumplimiento,
        'clientes_progreso': clientes_progreso,
        'clientes': clientes,
    })


@login_required
@login_required
def reportes_nps(request):
    if get_user_role(request.user) == 'cliente':
        messages.error(request, 'No tienes permiso para ver reportes NPS.')
        return redirect('Consultorias:dashboard')
    consultores = Consultor.objects.all()
    reportes = []
    all_scores = []
    for c in consultores:
        nps = c.calcular_nps()
        sesiones_eval = c.sesiones.filter(calificacion_nps__isnull=False).order_by('-fecha_inicio')
        for s in sesiones_eval:
            all_scores.append(s.calificacion_nps)
        reportes.append({
            'consultor': c,
            'nps': nps,
            'sesiones_evaluadas': sesiones_eval
        })

    total_evaluaciones = len(all_scores)
    if total_evaluaciones > 0:
        promotores = sum(1 for sc in all_scores if sc >= 9)
        detractores = sum(1 for sc in all_scores if sc <= 6)
        global_nps = round(((promotores - detractores) / total_evaluaciones) * 100, 1)
        global_promedio = round(sum(all_scores) / total_evaluaciones, 1)
    else:
        global_nps = 0.0
        global_promedio = 0.0

    return render(request, 'reportes_nps.html', {
        'reportes_nps': reportes,
        'global_nps': global_nps,
        'global_promedio': global_promedio,
        'total_evaluaciones': total_evaluaciones,
    })


def generar_pdf_nps(request, consultores):
    reportes = []
    all_scores = []
    for c in consultores:
        nps = c.calcular_nps()
        sesiones_eval = c.sesiones.filter(calificacion_nps__isnull=False).order_by('-fecha_inicio')
        for s in sesiones_eval:
            all_scores.append(s.calificacion_nps)
        reportes.append({'consultor': c, 'nps': nps, 'sesiones_evaluadas': sesiones_eval})

    total_evaluaciones = len(all_scores)
    if total_evaluaciones > 0:
        promotores = sum(1 for sc in all_scores if sc >= 9)
        detractores = sum(1 for sc in all_scores if sc <= 6)
        global_nps = round(((promotores - detractores) / total_evaluaciones) * 100, 1)
        global_promedio = round(sum(all_scores) / total_evaluaciones, 1)
    else:
        global_nps = 0.0
        global_promedio = 0.0

    template = get_template('reportes_nps_pdf.html')
    html = template.render({
        'reportes_nps': reportes,
        'global_nps': global_nps,
        'global_promedio': global_promedio,
        'total_evaluaciones': total_evaluaciones,
    })
    result = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=result)
    return result.getvalue()


@login_required
def reportes_nps_pdf(request):
    if get_user_role(request.user) == 'cliente':
        return HttpResponse('Sin permiso', status=403)
    consultores = Consultor.objects.all()
    reportes = []
    all_scores = []
    for c in consultores:
        nps = c.calcular_nps()
        sesiones_eval = c.sesiones.filter(calificacion_nps__isnull=False).order_by('-fecha_inicio')
        for s in sesiones_eval:
            all_scores.append(s.calificacion_nps)
        reportes.append({'consultor': c, 'nps': nps, 'sesiones_evaluadas': sesiones_eval})

    total_evaluaciones = len(all_scores)
    if total_evaluaciones > 0:
        promotores = sum(1 for sc in all_scores if sc >= 9)
        detractores = sum(1 for sc in all_scores if sc <= 6)
        global_nps = round(((promotores - detractores) / total_evaluaciones) * 100, 1)
        global_promedio = round(sum(all_scores) / total_evaluaciones, 1)
    else:
        global_nps = 0.0
        global_promedio = 0.0

    fecha_generacion = timezone.localtime().strftime('%d/%m/%Y %H:%M')
    qr_text = (
        'Mentor Consultorías\n'
        'Reporte de Satisfacción NPS\n'
        f'NPS global: {global_nps}%\n'
        f'Promedio: {global_promedio} / 10\n'
        f'Total de evaluaciones: {total_evaluaciones}\n'
        f'Generado: {fecha_generacion}'
    )
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    qr_buffer = io.BytesIO()
    qr.make_image(fill_color='black', back_color='white').save(qr_buffer, format='PNG')
    qr_data_uri = 'data:image/png;base64,' + base64.b64encode(qr_buffer.getvalue()).decode('ascii')

    return render(request, 'reportes_nps_print.html', {
        'reportes_nps': reportes,
        'global_nps': global_nps,
        'global_promedio': global_promedio,
        'total_evaluaciones': total_evaluaciones,
        'fecha_generacion': fecha_generacion,
        'qr_data_uri': qr_data_uri,
    })


@login_required
@require_POST
def enviar_reporte_nps(request):
    if get_user_role(request.user) == 'cliente':
        return JsonResponse({'success': False, 'error': 'No tienes permiso para enviar este reporte.'}, status=403)

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return JsonResponse({
            'success': False,
            'error': 'El correo no está configurado en el servidor. Revisa EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en Render.',
        }, status=503)

    try:
        consultores = Consultor.objects.all()
        pdf = generar_pdf_nps(request, consultores)
        email = EmailMessage(
            'Reporte NPS - Mentor Consultorías',
            'Adjunto el reporte NPS de consultores.',
            settings.EMAIL_HOST_USER,
            ['cristophereduardo2004@gmail.com'],
        )
        email.attach('reporte_nps.pdf', pdf, 'application/pdf')
        email.send(fail_silently=False)
        return JsonResponse({
            'success': True,
            'message': 'Reporte enviado a cristophereduardo2004@gmail.com.',
        })
    except Exception:
        logger.exception('No se pudo enviar el reporte NPS por correo')
        return JsonResponse({
            'success': False,
            'error': 'No se pudo enviar el correo. Verifica las credenciales SMTP configuradas en Render.',
        }, status=502)


@login_required
def calificar_nps(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        cliente = request.user.clientementoreado
        sesiones = SesionMentoria.objects.filter(
            Q(cliente=cliente) | Q(clientes_grupales=cliente),
            estado='COMPLETADA'
        ).order_by('-fecha_inicio')
    else:
        sesiones = SesionMentoria.objects.filter(estado='COMPLETADA').order_by('-fecha_inicio')

    if request.method == 'POST':
        sesion_id = request.POST.get('sesion_id')
        calificacion = request.POST.get('calificacion_nps')
        feedback = request.POST.get('feedback_cliente', '')
        sesion = get_object_or_404(SesionMentoria, id=sesion_id)
        if role == 'cliente':
            cliente = request.user.clientementoreado
            if sesion.cliente != cliente and cliente not in sesion.clientes_grupales.all():
                return JsonResponse({'success': False, 'error': 'No tienes permiso para calificar esta sesión.'}, status=403)
        if calificacion and calificacion.isdigit():
            sesion.calificacion_nps = int(calificacion)
        sesion.feedback_cliente = feedback
        sesion.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('Consultorias:calificar_nps')

    return render(request, 'calificar_nps.html', {'sesiones': sesiones})


# --- FUNCIONALIDADES REQUERIDAS ---

# 1. FullCalendar
@login_required
def calendario(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        cliente = request.user.clientementoreado
        consultores = Consultor.objects.filter(id=cliente.consultor.id, estado='ACTIVO')
        clientes = ClienteMentoreado.objects.filter(id=cliente.id, estado='ACTIVO')
    elif role == 'consultor':
        consultor = request.user.consultor
        consultores = Consultor.objects.filter(id=consultor.id, estado='ACTIVO')
        clientes = consultor.clientes.filter(estado='ACTIVO')
    else:
        consultores = Consultor.objects.filter(estado='ACTIVO')
        clientes = ClienteMentoreado.objects.filter(estado='ACTIVO')
    return render(request, 'calendario.html', {'consultores': consultores, 'clientes': clientes})


# 2. jQuery UI Sortable
@login_required
def plan_trabajo(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        clientes = ClienteMentoreado.objects.filter(id=request.user.clientementoreado.id)
    elif role == 'consultor':
        clientes = request.user.consultor.clientes.all()
    else:
        clientes = ClienteMentoreado.objects.all()

    cliente_id = request.GET.get('cliente_id')
    if cliente_id and role != 'cliente':
        cliente_seleccionado = get_object_or_404(ClienteMentoreado, id=cliente_id)
    else:
        cliente_seleccionado = clientes.first()

    objetivos = cliente_seleccionado.objetivos.all().order_by('prioridad') if cliente_seleccionado else []

    return render(request, 'plan_trabajo.html', {
        'clientes': clientes,
        'cliente_seleccionado': cliente_seleccionado,
        'cliente': cliente_seleccionado,
        'objetivos': objetivos,
    })


# 3. Hotkeys-js Notas
@login_required
def notas_sesion(request, sesion_id=None):
    role = get_user_role(request.user)
    if role == 'consultor':
        consultor = request.user.consultor
        sesiones = consultor.sesiones.all()
    elif role == 'cliente':
        cliente = request.user.clientementoreado
        sesiones = SesionMentoria.objects.filter(
            Q(cliente=cliente) | Q(clientes_grupales=cliente)
        )
    else:
        sesiones = SesionMentoria.objects.all()

    if sesion_id:
        sesion_seleccionada = get_object_or_404(SesionMentoria, id=sesion_id)
    else:
        sesion_seleccionada = sesiones.first()

    sesiones = sesiones.order_by('-fecha_inicio')

    return render(request, 'notas_sesion.html', {
        'sesiones': sesiones,
        'sesion_seleccionada': sesion_seleccionada,
        'sesion': sesion_seleccionada,
    })


# 4. Driver.js Tour
@login_required
def avances_cliente(request):
    role = get_user_role(request.user)
    if role != 'cliente':
        messages.error(request, 'Solo los clientes pueden subir avances.')
        return redirect('Consultorias:dashboard')
    clientes = ClienteMentoreado.objects.filter(id=request.user.clientementoreado.id)

    cliente_id = request.GET.get('cliente_id')
    if cliente_id and role != 'cliente':
        cliente = get_object_or_404(ClienteMentoreado, id=cliente_id)
    else:
        cliente = clientes.first()

    objetivos = cliente.objetivos.all() if cliente else []
    entregables = cliente.entregables.all() if cliente else []

    return render(request, 'avances_cliente.html', {
        'clientes': clientes,
        'cliente': cliente,
        'objetivos': objetivos,
        'entregables': entregables,
    })


# --- CRUD SIMPLE DE ENTIDADES ---

# Consultores
@login_required
def consultores_lista(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        consultores = Consultor.objects.filter(id=request.user.clientementoreado.consultor.id)
    elif role == 'consultor':
        consultores = Consultor.objects.filter(id=request.user.consultor.id)
    else:
        consultores = Consultor.objects.all()
    return render(request, 'consultores/lista.html', {'consultores': consultores})

@login_required
def consultor_crear(request):
    role = get_user_role(request.user)
    if role not in ('admin', 'consultor'):
        messages.error(request, 'No tienes permiso para crear consultores.')
        return redirect('Consultorias:consultores_lista')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        especialidad = request.POST.get('especialidad', '').strip()
        email = request.POST.get('email', '').strip()

        errors = {}
        if not nombre:
            errors['nombre'] = 'El nombre es obligatorio.'
        if not especialidad:
            errors['especialidad'] = 'La especialidad es obligatoria.'
        if not email:
            errors['email'] = 'El correo electrónico es obligatorio.'

        if errors:
            return render(request, 'consultores/form.html', {
                'form_data': request.POST, 'errors': errors
            })

        Consultor.objects.create(
            nombre=nombre,
            especialidad=especialidad,
            email=email,
            telefono=request.POST.get('telefono', ''),
            tarifa_hora=request.POST.get('tarifa_hora', 50.0),
        )
        return redirect('Consultorias:consultores_lista')
    return render(request, 'consultores/form.html')

@login_required
def consultor_editar(request, pk):
    c = get_object_or_404(Consultor, pk=pk)
    if request.method == 'POST':
        c.nombre = request.POST.get('nombre')
        c.especialidad = request.POST.get('especialidad')
        c.email = request.POST.get('email')
        c.telefono = request.POST.get('telefono', '')
        c.tarifa_hora = request.POST.get('tarifa_hora', 50.0)
        c.estado = request.POST.get('estado', 'ACTIVO')
        c.biografia = request.POST.get('biografia', '')
        c.save()
        return redirect('Consultorias:consultores_lista')
    return render(request, 'consultores/form.html', {'consultor': c})

@login_required
def consultor_eliminar(request, pk):
    c = get_object_or_404(Consultor, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Validacion: no permitir eliminar si esta en una sesion programada o tiene clientes activos
    sesiones_activas = c.sesiones.filter(estado='PROGRAMADA').exists()
    clientes_activos = c.clientes.filter(estado='ACTIVO').exists()
    if sesiones_activas or clientes_activos:
        motivo = "No se puede eliminar el consultor porque tiene sesiones programadas o clientes activos asignados."
        if is_ajax:
            return JsonResponse({'success': False, 'error': motivo}, status=400)
        messages.error(request, motivo)
        return redirect('Consultorias:consultores_lista')

    if request.method == 'POST':
        c.delete()
        if is_ajax:
            return JsonResponse({'success': True})
        messages.success(request, 'Consultor eliminado correctamente.')
        return redirect('Consultorias:consultores_lista')
    return render(request, 'consultores/confirmar_eliminar.html', {'consultor': c})


# Clientes
@login_required
def clientes_lista(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        clientes = ClienteMentoreado.objects.filter(id=request.user.clientementoreado.id)
    elif role == 'consultor':
        clientes = request.user.consultor.clientes.all()
    else:
        clientes = ClienteMentoreado.objects.all()
    return render(request, 'clientes/lista.html', {'clientes': clientes})

@login_required
def cliente_crear(request):
    role = get_user_role(request.user)
    if role == 'consultor':
        consultores = Consultor.objects.filter(id=request.user.consultor.id)
    else:
        consultores = Consultor.objects.all()
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        empresa = request.POST.get('empresa', '').strip()
        sector = request.POST.get('sector', '').strip()
        email = request.POST.get('email', '').strip()
        consultor_id = request.POST.get('consultor_id', '').strip()

        errors = {}
        if not nombre:
            errors['nombre'] = 'El nombre es obligatorio.'
        if not empresa:
            errors['empresa'] = 'La empresa es obligatoria.'
        if not sector:
            errors['sector'] = 'El sector es obligatorio.'
        if not email:
            errors['email'] = 'El correo electrónico es obligatorio.'
        if not consultor_id:
            errors['consultor_id'] = 'Debe seleccionar un consultor.'

        if errors:
            return render(request, 'clientes/form.html', {
                'consultores': consultores, 'form_data': request.POST, 'errors': errors
            })

        cons = get_object_or_404(Consultor, id=consultor_id)
        ClienteMentoreado.objects.create(
            nombre=nombre,
            empresa=empresa,
            sector=sector,
            email=email,
            telefono=request.POST.get('telefono', ''),
            consultor=cons,
        )
        return redirect('Consultorias:clientes_lista')
    return render(request, 'clientes/form.html', {'consultores': consultores})

@login_required
def cliente_editar(request, pk):
    cli = get_object_or_404(ClienteMentoreado, pk=pk)
    role = get_user_role(request.user)
    if role == 'consultor':
        consultores = Consultor.objects.filter(id=request.user.consultor.id)
    else:
        consultores = Consultor.objects.all()
    if request.method == 'POST':
        cli.nombre = request.POST.get('nombre')
        cli.empresa = request.POST.get('empresa')
        cli.sector = request.POST.get('sector')
        cli.email = request.POST.get('email')
        cli.consultor = get_object_or_404(Consultor, id=request.POST.get('consultor_id'))
        cli.estado = request.POST.get('estado', 'ACTIVO')
        cli.save()
        return redirect('Consultorias:clientes_lista')
    return render(request, 'clientes/form.html', {'cliente': cli, 'consultores': consultores})

@login_required
def cliente_eliminar(request, pk):
    cli = get_object_or_404(ClienteMentoreado, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Validacion: no permitir eliminar si tiene sesiones programadas u objetivos pendientes
    sesiones_activas = cli.sesiones_individuales.filter(estado='PROGRAMADA').exists()
    objetivos_activos = cli.objetivos.filter(estado__in=['PENDIENTE', 'EN_PROCESO']).exists()
    if sesiones_activas or objetivos_activos:
        motivo = "No se puede eliminar el cliente porque tiene sesiones programadas u objetivos pendientes en su plan."
        if is_ajax:
            return JsonResponse({'success': False, 'error': motivo}, status=400)
        messages.error(request, motivo)
        return redirect('Consultorias:clientes_lista')

    if request.method == 'POST':
        cli.delete()
        if is_ajax:
            return JsonResponse({'success': True})
        messages.success(request, 'Cliente eliminado correctamente.')
        return redirect('Consultorias:clientes_lista')
    return render(request, 'clientes/confirmar_eliminar.html', {'cliente': cli})


# Sesiones
@login_required
def sesiones_lista(request):
    role = get_user_role(request.user)
    if role == 'consultor':
        sesiones = request.user.consultor.sesiones.all()
    elif role == 'cliente':
        cliente = request.user.clientementoreado
        sesiones = SesionMentoria.objects.filter(
            Q(cliente=cliente) | Q(clientes_grupales=cliente)
        )
    else:
        sesiones = SesionMentoria.objects.all()
    return render(request, 'sesiones/lista.html', {'sesiones': sesiones.order_by('-fecha_inicio')})

@login_required
def sesion_crear(request):
    role = get_user_role(request.user)
    if role == 'consultor':
        consultor = request.user.consultor
        consultores = Consultor.objects.filter(id=consultor.id)
        clientes = consultor.clientes.all()
    elif role == 'cliente':
        messages.error(request, 'No tienes permiso para crear sesiones.')
        return redirect('Consultorias:sesiones_lista')
    else:
        consultores = Consultor.objects.all()
        clientes = ClienteMentoreado.objects.all()
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        consultor_id = request.POST.get('consultor_id', '').strip()
        fecha_inicio = request.POST.get('fecha_inicio', '').strip()
        fecha_fin = request.POST.get('fecha_fin', '').strip()

        errors = {}
        if not titulo:
            errors['titulo'] = 'El título es obligatorio.'
        if not consultor_id:
            errors['consultor_id'] = 'Debe seleccionar un consultor.'
        if not fecha_inicio:
            errors['fecha_inicio'] = 'La fecha de inicio es obligatoria.'
        if not fecha_fin:
            errors['fecha_fin'] = 'La fecha de fin es obligatoria.'
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            errors['fecha_fin'] = 'La fecha de fin debe ser posterior a la de inicio.'

        if errors:
            return render(request, 'sesiones/form.html', {
                'consultores': consultores, 'clientes': clientes,
                'form_data': request.POST, 'errors': errors
            })

        c_id = request.POST.get('cliente_id')
        cli = get_object_or_404(ClienteMentoreado, id=c_id) if c_id else None
        cons = get_object_or_404(Consultor, id=consultor_id)
        
        SesionMentoria.objects.create(
            titulo=titulo,
            tipo=request.POST.get('tipo', 'INDIVIDUAL'),
            consultor=cons,
            cliente=cli,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modalidad=request.POST.get('modalidad', 'VIRTUAL')
        )
        return redirect('Consultorias:sesiones_lista')
    return render(request, 'sesiones/form.html', {'consultores': consultores, 'clientes': clientes})

@login_required
def sesion_editar(request, pk):
    s = get_object_or_404(SesionMentoria, pk=pk)
    consultores = Consultor.objects.all()
    clientes = ClienteMentoreado.objects.all()
    if request.method == 'POST':
        s.titulo = request.POST.get('titulo')
        s.tipo = request.POST.get('tipo', 'INDIVIDUAL')
        s.consultor = get_object_or_404(Consultor, id=request.POST.get('consultor_id'))
        c_id = request.POST.get('cliente_id')
        s.cliente = get_object_or_404(ClienteMentoreado, id=c_id) if c_id else None
        s.fecha_inicio = request.POST.get('fecha_inicio')
        s.fecha_fin = request.POST.get('fecha_fin')
        s.estado = request.POST.get('estado', 'PROGRAMADA')
        nps = request.POST.get('calificacion_nps')
        if nps:
            s.calificacion_nps = int(nps)
        s.feedback_cliente = request.POST.get('feedback_cliente', '')
        s.save()
        return redirect('Consultorias:sesiones_lista')
    return render(request, 'sesiones/form.html', {'sesion': s, 'consultores': consultores, 'clientes': clientes})

@login_required
def sesion_eliminar(request, pk):
    s = get_object_or_404(SesionMentoria, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Validacion: no borrar sesion si esta programada y activa
    if s.estado == 'PROGRAMADA':
        motivo = "No se puede eliminar una sesión programada en curso. Márquela como cancelada o completada antes."
        if is_ajax:
            return JsonResponse({'success': False, 'error': motivo}, status=400)
        messages.error(request, motivo)
        return redirect('Consultorias:sesiones_lista')

    if request.method == 'POST':
        s.delete()
        if is_ajax:
            return JsonResponse({'success': True})
        messages.success(request, 'Sesión eliminada correctamente.')
        return redirect('Consultorias:sesiones_lista')
    return render(request, 'sesiones/confirmar_eliminar.html', {'sesion': s})


# Objetivos
@login_required
def objetivos_lista(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        objetivos = Objetivo.objects.filter(cliente=request.user.clientementoreado)
    elif role == 'consultor':
        objetivos = Objetivo.objects.filter(cliente__consultor=request.user.consultor)
    else:
        objetivos = Objetivo.objects.all()
    return render(request, 'objetivos/lista.html', {'objetivos': objetivos})

@login_required
def objetivo_crear(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        clientes = ClienteMentoreado.objects.filter(id=request.user.clientementoreado.id)
    else:
        clientes = ClienteMentoreado.objects.all()
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        cliente_id = request.POST.get('cliente_id', '').strip()

        errors = {}
        if not cliente_id:
            errors['cliente_id'] = 'Debe seleccionar un cliente.'
        if not titulo:
            errors['titulo'] = 'El título del hito es obligatorio.'

        if errors:
            return render(request, 'objetivos/form.html', {
                'clientes': clientes, 'form_data': request.POST, 'errors': errors
            })

        cli = get_object_or_404(ClienteMentoreado, id=cliente_id)
        if role == 'cliente' and cli.id != request.user.clientementoreado.id:
            errors['cliente_id'] = 'No tienes permiso para crear hitos para otro cliente.'
            return render(request, 'objetivos/form.html', {
                'clientes': clientes, 'form_data': request.POST, 'errors': errors
            })
        prio = cli.objetivos.count() + 1
        Objetivo.objects.create(
            cliente=cli,
            titulo=titulo,
            descripcion=request.POST.get('descripcion', ''),
            prioridad=prio,
            estado=request.POST.get('estado', 'PENDIENTE')
        )
        return redirect('Consultorias:plan_trabajo')
    return render(request, 'objetivos/form.html', {'clientes': clientes})

@login_required
def objetivo_editar(request, pk):
    obj = get_object_or_404(Objetivo, pk=pk)
    role = get_user_role(request.user)
    if role == 'cliente':
        if obj.cliente.id != request.user.clientementoreado.id:
            messages.error(request, 'No tienes permiso para editar este hito.')
            return redirect('Consultorias:plan_trabajo')
        clientes = ClienteMentoreado.objects.filter(id=obj.cliente.id)
    else:
        clientes = ClienteMentoreado.objects.all()
    if request.method == 'POST':
        obj.titulo = request.POST.get('titulo')
        obj.descripcion = request.POST.get('descripcion', '')
        obj.estado = request.POST.get('estado', 'PENDIENTE')
        obj.save()
        return redirect('Consultorias:plan_trabajo')
    return render(request, 'objetivos/form.html', {'objetivo': obj, 'clientes': clientes})

@login_required
def objetivo_eliminar(request, pk):
    obj = get_object_or_404(Objetivo, pk=pk)
    role = get_user_role(request.user)
    if role == 'cliente' and obj.cliente.id != request.user.clientementoreado.id:
        messages.error(request, 'No tienes permiso para eliminar este hito.')
        return redirect('Consultorias:plan_trabajo')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if obj.entregables.exists():
        motivo = "No se puede eliminar el objetivo porque tiene entregables asociados."
        if is_ajax:
            return JsonResponse({'success': False, 'error': motivo}, status=400)
        messages.error(request, motivo)
        return redirect('Consultorias:plan_trabajo')

    if request.method == 'POST':
        obj.delete()
        if is_ajax:
            return JsonResponse({'success': True})
        messages.success(request, 'Objetivo eliminado correctamente.')
        return redirect('Consultorias:plan_trabajo')
    return render(request, 'objetivos/confirmar_eliminar.html', {'objetivo': obj})


# Entregables
@login_required
def entregables_lista(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        entregables = Entregable.objects.filter(cliente=request.user.clientementoreado)
    elif role == 'consultor':
        entregables = Entregable.objects.filter(cliente__consultor=request.user.consultor)
    else:
        entregables = Entregable.objects.all()
    return render(request, 'entregables/lista.html', {'entregables': entregables})

@login_required
def entregable_crear(request):
    clientes = ClienteMentoreado.objects.all()
    objetivos = Objetivo.objects.all()
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        cliente_id = request.POST.get('cliente_id', '').strip()
        objetivo_id = request.POST.get('objetivo_id', '').strip()
        archivo = request.FILES.get('archivo')

        errors = {}
        if not cliente_id:
            errors['cliente_id'] = 'Debe seleccionar un cliente.'
        if not objetivo_id:
            errors['objetivo_id'] = 'Debe seleccionar un hito.'
        if not titulo:
            errors['titulo'] = 'El título es obligatorio.'
        if archivo and not archivo.name.lower().endswith('.pdf'):
            errors['archivo'] = 'Solo se permiten archivos PDF.'
        if not archivo:
            errors['archivo'] = 'Debe adjuntar un archivo PDF.'

        if errors:
            return render(request, 'entregables/form.html', {
                'clientes': clientes, 'objetivos': objetivos,
                'form_data': request.POST, 'errors': errors
            })

        cli = get_object_or_404(ClienteMentoreado, id=cliente_id)
        obj = get_object_or_404(Objetivo, id=objetivo_id)
        Entregable.objects.create(
            cliente=cli,
            objetivo=obj,
            titulo=titulo,
            descripcion=request.POST.get('descripcion', ''),
            archivo=archivo
        )
        return redirect('Consultorias:avances_cliente')
    return render(request, 'entregables/form.html', {'clientes': clientes, 'objetivos': objetivos})

@login_required
def entregable_editar(request, pk):
    ent = get_object_or_404(Entregable, pk=pk)
    if request.method == 'POST':
        ent.estado = request.POST.get('estado', 'PENDIENTE')
        ent.comentarios_consultor = request.POST.get('comentarios_consultor', '')
        ent.save()
        return redirect('Consultorias:entregables_lista')
    return render(request, 'entregables/form.html', {'entregable': ent})

@login_required
def entregable_eliminar(request, pk):
    ent = get_object_or_404(Entregable, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST':
        ent.delete()
        if is_ajax:
            return JsonResponse({'success': True})
        messages.success(request, 'Entregable eliminado correctamente.')
        return redirect('Consultorias:entregables_lista')
    return render(request, 'entregables/confirmar_eliminar.html', {'entregable': ent})



# --- ENDPOINTS API SIMPLE ---

@login_required
def api_sesiones_eventos(request):
    role = get_user_role(request.user)
    if role == 'consultor':
        sesiones = request.user.consultor.sesiones.all()
    elif role == 'cliente':
        cliente = request.user.clientementoreado
        sesiones = SesionMentoria.objects.filter(
            Q(cliente=cliente) | Q(clientes_grupales=cliente)
        )
    else:
        sesiones = SesionMentoria.objects.all()
    eventos = [s.to_dict() for s in sesiones]
    return JsonResponse(eventos, safe=False)


@login_required
def api_sesion_guardar(request):
    role = get_user_role(request.user)
    if role == 'cliente':
        return JsonResponse({'success': False, 'error': 'No tienes permiso para crear sesiones.'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fecha_inicio = timezone.datetime.fromisoformat(data.get('fecha_inicio', ''))
            fecha_fin = timezone.datetime.fromisoformat(data.get('fecha_fin', ''))
            if timezone.is_naive(fecha_inicio):
                fecha_inicio = timezone.make_aware(fecha_inicio)
            if timezone.is_naive(fecha_fin):
                fecha_fin = timezone.make_aware(fecha_fin)
        except (json.JSONDecodeError, TypeError, ValueError):
            return JsonResponse({
                'success': False,
                'error': 'Las fechas ingresadas no son válidas.'
            }, status=400)

        if timezone.localtime(fecha_inicio).date() < timezone.localdate():
            return JsonResponse({
                'success': False,
                'error': 'No se puede agendar una sesión en una fecha anterior a hoy.'
            }, status=400)

        if fecha_fin <= fecha_inicio:
            return JsonResponse({
                'success': False,
                'error': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            }, status=400)

        cons = get_object_or_404(Consultor, id=data.get('consultor_id'))
        cli_id = data.get('cliente_id')
        cli = get_object_or_404(ClienteMentoreado, id=cli_id) if cli_id else None

        SesionMentoria.objects.create(
            titulo=data.get('titulo'),
            tipo=data.get('tipo', 'INDIVIDUAL'),
            consultor=cons,
            cliente=cli,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modalidad=data.get('modalidad', 'VIRTUAL')
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def api_objetivos_reordenar(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        orden_ids = data.get('orden_ids', [])
        for idx, obj_id in enumerate(orden_ids, start=1):
            Objetivo.objects.filter(id=obj_id).update(prioridad=idx)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def api_notas_guardar(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        sesion = get_object_or_404(SesionMentoria, id=data.get('sesion_id'))
        sesion.notas_sesion = data.get('notas', '')
        if data.get('estado'):
            sesion.estado = data.get('estado')
        sesion.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def api_entregable_subir(request):
    if request.method == 'POST':
        cli = get_object_or_404(ClienteMentoreado, id=request.POST.get('cliente_id'))
        obj = get_object_or_404(Objetivo, id=request.POST.get('objetivo_id'))
        Entregable.objects.create(
            cliente=cli,
            objetivo=obj,
            titulo=request.POST.get('titulo'),
            descripcion=request.POST.get('descripcion', ''),
            archivo=request.FILES.get('archivo')
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
