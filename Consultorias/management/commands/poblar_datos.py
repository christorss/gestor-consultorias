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

        for cli, tit, desc, prio, est, prog in obj_data:
            Objetivo.objects.get_or_create(
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

        # 4. Entregables
        o1 = Objetivo.objects.filter(cliente=cli1).first()
        if o1:
            Entregable.objects.get_or_create(
                objetivo=o1,
                cliente=cli1,
                titulo='Plan_Financiero_v1.pdf',
                defaults={
                    'descripcion': 'Archivo del plan financiero en formato PDF.',
                    'enlace_externo': 'https://drive.google.com/ejemplo',
                    'estado': 'APROBADO',
                    'comentarios_consultor': 'Buen trabajo en los cálculos.'
                }
            )

        # 5. Sesiones con NPS
        now = timezone.now()
        
        SesionMentoria.objects.get_or_create(
            titulo='Reunión de avance financiero',
            consultor=c1,
            cliente=cli1,
            defaults={
                'tipo': 'INDIVIDUAL',
                'fecha_inicio': now - timedelta(days=5),
                'fecha_fin': now - timedelta(days=5, hours=-1),
                'modalidad': 'VIRTUAL',
                'enlace_reunion': 'https://meet.google.com/abc-123',
                'estado': 'COMPLETADA',
                'notas_sesion': 'Se revisó el flujo de caja del primer trimestre.',
                'calificacion_nps': 10,
                'feedback_cliente': 'Excelente sesión de ayuda.'
            }
        )

        SesionMentoria.objects.get_or_create(
            titulo='Asesoría de impuestos y presupuesto',
            consultor=c2,
            cliente=cli2,
            defaults={
                'tipo': 'INDIVIDUAL',
                'fecha_inicio': now - timedelta(days=2),
                'fecha_fin': now - timedelta(days=2, hours=-1),
                'modalidad': 'VIRTUAL',
                'enlace_reunion': 'https://meet.google.com/xyz-789',
                'estado': 'COMPLETADA',
                'notas_sesion': 'Revisión de facturas y gastos mensuales.',
                'calificacion_nps': 9,
                'feedback_cliente': 'Muy clara la explicación.'
            }
        )

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

        self.stdout.write("Datos de prueba cargados correctamente.")
        self.stdout.write("Usuarios: admin/admin123, consultor/consultor123, cliente/cliente123")
