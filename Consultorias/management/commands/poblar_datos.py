from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from Consultorias.models import Consultor, ClienteMentoreado, Objetivo, Entregable, SesionMentoria


class Command(BaseCommand):
    help = 'Carga datos de prueba para el proyecto de consultorias'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cargando datos de prueba...")

        # Usuario admin de prueba
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@mail.com', 'admin123')
            self.stdout.write("Superusuario creado: admin / admin123")

        # 1. Consultores
        c1, _ = Consultor.objects.get_or_create(
            email='carlos.mendoza@mail.com',
            defaults={
                'nombre': 'Carlos Mendoza',
                'especialidad': 'Estrategia de Negocios',
                'telefono': '0991234567',
                'biografia': 'Consultor en gestión estratégica y planes de negocio.',
                'tarifa_hora': 50.00,
                'estado': 'ACTIVO'
            }
        )

        c2, _ = Consultor.objects.get_or_create(
            email='elena.rostova@mail.com',
            defaults={
                'nombre': 'Elena Rostova',
                'especialidad': 'Finanzas y Contabilidad',
                'telefono': '0987654321',
                'biografia': 'Asesora financiera para pequeñas y medianas empresas.',
                'tarifa_hora': 60.00,
                'estado': 'ACTIVO'
            }
        )

        c3, _ = Consultor.objects.get_or_create(
            email='roberto.gomez@mail.com',
            defaults={
                'nombre': 'Roberto Gómez',
                'especialidad': 'Marketing y Ventas',
                'telefono': '0998887777',
                'biografia': 'Especialista en ventas y publicidad digital.',
                'tarifa_hora': 45.00,
                'estado': 'ACTIVO'
            }
        )

        # 2. Clientes
        cli1, _ = ClienteMentoreado.objects.get_or_create(
            email='contacto@biotech.ec',
            defaults={
                'nombre': 'Sofía Aulestia',
                'empresa': 'BioTech Solutions',
                'sector': 'Tecnología',
                'telefono': '0991112222',
                'consultor': c1,
                'estado': 'ACTIVO'
            }
        )

        cli2, _ = ClienteMentoreado.objects.get_or_create(
            email='gerencia@innovaretail.com',
            defaults={
                'nombre': 'David Morales',
                'empresa': 'Innova Retail',
                'sector': 'Comercio',
                'telefono': '0993334444',
                'consultor': c2,
                'estado': 'ACTIVO'
            }
        )

        cli3, _ = ClienteMentoreado.objects.get_or_create(
            email='info@ecofood.ec',
            defaults={
                'nombre': 'Lucía Cárdenas',
                'empresa': 'EcoFood',
                'sector': 'Alimentos',
                'telefono': '0995556666',
                'consultor': c3,
                'estado': 'ACTIVO'
            }
        )

        # 3. Objetivos / Hitos
        obj_data = [
            (cli1, 'Diseño del Plan Financiero', 'Elaboración del presupuesto y flujo de caja', 1, 'COMPLETADO', 100),
            (cli1, 'Definición de Propuesta de Valor', 'Analizar ventajas competitivas del producto', 2, 'EN_PROCESO', 60),
            (cli1, 'Presentación a Inversionistas', 'Preparar la presentación del proyecto', 3, 'PENDIENTE', 0),

            (cli2, 'Auditoría de Ventas', 'Revisión del proceso de ventas de la empresa', 1, 'COMPLETADO', 100),
            (cli2, 'Implementar Sistema CRM', 'Configuración de base de datos de clientes', 2, 'EN_PROCESO', 40),

            (cli3, 'Estudio de Mercado', 'Encuestas a clientes potenciales', 1, 'COMPLETADO', 100),
            (cli3, 'Rediseño de Marca', 'Diseño de nuevo logotipo y empaques', 2, 'PENDIENTE', 0),
        ]

        objetivos = {}
        for cli, tit, desc, prio, est, prog in obj_data:
            objetivo, _ = Objetivo.objects.get_or_create(
                cliente=cli,
                titulo=tit,
                defaults={
                    'descripcion': desc,
                    'prioridad': prio,
                    'estado': est,
                    'progreso_porcentaje': prog,
                    'fecha_limite': timezone.now().date() + timedelta(days=prio*10)
                }
            )
            objetivos[(cli.email, tit)] = objetivo

        # 4. Entregables
        entregables_data = [
            (
                cli1, 'Diseño del Plan Financiero', 'Plan financiero y flujo de caja',
                'Documento con presupuesto, proyecciones y flujo de caja del primer año.',
                'APROBADO', 'Cálculos claros y supuestos correctamente sustentados.'
            ),
            (
                cli1, 'Definición de Propuesta de Valor', 'Matriz de propuesta de valor',
                'Análisis de segmentos, necesidades y diferenciadores del producto.',
                'EN_REVISION', 'Agregar evidencia de las entrevistas realizadas a clientes.'
            ),
            (
                cli2, 'Auditoría de Ventas', 'Informe de auditoría comercial',
                'Diagnóstico del embudo comercial y oportunidades de mejora.',
                'APROBADO', 'El diagnóstico identifica correctamente los cuellos de botella.'
            ),
            (
                cli2, 'Implementar Sistema CRM', 'Plan de implementación del CRM',
                'Cronograma, responsables y estructura inicial de la base de clientes.',
                'PENDIENTE', ''
            ),
            (
                cli3, 'Estudio de Mercado', 'Resultados del estudio de mercado',
                'Resumen de encuestas, perfiles de cliente y conclusiones principales.',
                'APROBADO', 'Resultados bien presentados y útiles para la toma de decisiones.'
            ),
        ]
        for cli, objetivo_titulo, titulo, descripcion, estado, comentario in entregables_data:
            objetivo = objetivos[(cli.email, objetivo_titulo)]
            Entregable.objects.get_or_create(
                objetivo=objetivo,
                cliente=cli,
                titulo=titulo,
                defaults={
                    'descripcion': descripcion,
                    'estado': estado,
                    'comentarios_consultor': comentario
                }
            )

        # 5. Sesiones con NPS
        now = timezone.now()
        sesiones_data = [
            ('Diagnóstico estratégico inicial', c1, cli1, -30, 'PRESENCIAL', 'COMPLETADA', 9,
             'Se definieron prioridades y riesgos del modelo de negocio.', 'La sesión permitió ordenar nuestras prioridades.'),
            ('Revisión del plan financiero', c1, cli1, -12, 'VIRTUAL', 'COMPLETADA', 10,
             'Se revisaron presupuesto, flujo de caja y punto de equilibrio.', 'Excelente orientación y recomendaciones prácticas.'),
            ('Preparación para inversionistas', c1, cli1, 7, 'PRESENCIAL', 'PROGRAMADA', None,
             'Se trabajará la narrativa y estructura de la presentación.', ''),
            ('Auditoría del proceso comercial', c2, cli2, -18, 'PRESENCIAL', 'COMPLETADA', 8,
             'Se analizaron indicadores, costos y desempeño del equipo comercial.', 'La información fue útil, aunque faltó tiempo para preguntas.'),
            ('Configuración inicial del CRM', c2, cli2, 4, 'VIRTUAL', 'PROGRAMADA', None,
             'Se configurarán etapas, campos y responsables del proceso.', ''),
            ('Análisis del estudio de mercado', c3, cli3, -9, 'VIRTUAL', 'COMPLETADA', 6,
             'Se revisaron segmentos, resultados de encuestas y competencia.', 'Necesitamos ejemplos más específicos para nuestro sector.'),
            ('Taller de posicionamiento de marca', c3, cli3, 10, 'PRESENCIAL', 'PROGRAMADA', None,
             'Taller para definir personalidad, mensajes y lineamientos de marca.', ''),
        ]

        for titulo, consultor, cliente, dias, modalidad, estado, nps, notas, feedback in sesiones_data:
            inicio = now + timedelta(days=dias)
            SesionMentoria.objects.get_or_create(
                titulo=titulo,
                consultor=consultor,
                cliente=cliente,
                defaults={
                    'tipo': 'INDIVIDUAL',
                    'fecha_inicio': inicio,
                    'fecha_fin': inicio + timedelta(hours=1),
                    'modalidad': modalidad,
                    'estado': estado,
                    'notas_sesion': notas,
                    'calificacion_nps': nps,
                    'feedback_cliente': feedback
                }
            )

        sesion_grupal, _ = SesionMentoria.objects.get_or_create(
            titulo='Taller grupal de planificación empresarial',
            consultor=c1,
            cliente=None,
            defaults={
                'tipo': 'GRUPAL',
                'fecha_inicio': now + timedelta(days=14),
                'fecha_fin': now + timedelta(days=14, hours=2),
                'modalidad': 'PRESENCIAL',
                'estado': 'PROGRAMADA',
                'notas_sesion': 'Taller colaborativo para construir planes de acción trimestrales.'
            }
        )
        sesion_grupal.clientes_grupales.set([cli1, cli2, cli3])

        # 6. Usuarios de prueba vinculados a perfiles
        u_consultor, _ = User.objects.get_or_create(
            username='consultor',
            defaults={'email': 'carlos.mendoza@mail.com', 'first_name': 'Carlos'}
        )
        u_consultor.set_password('consultor123')
        u_consultor.save()
        if not hasattr(u_consultor, 'consultor') or u_consultor.consultor is None:
            c1.user = u_consultor
            c1.save()

        u_cliente, _ = User.objects.get_or_create(
            username='cliente',
            defaults={'email': 'contacto@biotech.ec', 'first_name': 'Sofía'}
        )
        u_cliente.set_password('cliente123')
        u_cliente.save()
        if not hasattr(u_cliente, 'clientementoreado') or u_cliente.clientementoreado is None:
            cli1.user = u_cliente
            cli1.save()

        usuarios_adicionales = [
            ('consultor_finanzas', 'consultor123', 'elena.rostova@mail.com', c2, None),
            ('consultor_marketing', 'consultor123', 'roberto.gomez@mail.com', c3, None),
            ('cliente_retail', 'cliente123', 'gerencia@innovaretail.com', None, cli2),
            ('cliente_ecofood', 'cliente123', 'info@ecofood.ec', None, cli3),
        ]
        for username, password, email, consultor, cliente in usuarios_adicionales:
            usuario, creado = User.objects.get_or_create(username=username, defaults={'email': email})
            if creado:
                usuario.set_password(password)
                usuario.save()
            if consultor and consultor.user_id is None:
                consultor.user = usuario
                consultor.save()
            if cliente and cliente.user_id is None:
                cliente.user = usuario
                cliente.save()

        self.stdout.write("Datos de prueba cargados correctamente.")
        self.stdout.write("Se cargaron consultores, clientes, objetivos, entregables, sesiones y evaluaciones NPS.")
