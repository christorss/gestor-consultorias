from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from .views import enviar_reporte_nps


class EnviarReporteNpsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def request(self, method='post'):
        request = getattr(self.factory, method)('/reportes-nps/enviar/')
        request.user = self.user
        return request

    @override_settings(EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD='')
    @patch('Consultorias.views.get_user_role', return_value='admin')
    def test_informa_si_el_correo_no_esta_configurado(self, _role):
        response = enviar_reporte_nps(self.request())

        self.assertEqual(response.status_code, 503)
        self.assertIn('EMAIL_HOST_USER', response.content.decode())

    @override_settings(EMAIL_HOST_USER='correo@example.com', EMAIL_HOST_PASSWORD='clave')
    @patch('Consultorias.views.EmailMessage')
    @patch('Consultorias.views.generar_pdf_nps', return_value=b'pdf')
    @patch('Consultorias.views.get_user_role', return_value='admin')
    def test_envia_el_reporte_y_responde_json(self, _role, _pdf, email_message):
        email = MagicMock()
        email_message.return_value = email

        response = enviar_reporte_nps(self.request())

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': 'Reporte enviado a cristophereduardo2004@gmail.com.',
        })
        email.send.assert_called_once_with(fail_silently=False)

    @patch('Consultorias.views.get_user_role', return_value='admin')
    def test_solo_admite_post(self, _role):
        response = enviar_reporte_nps(self.request('get'))

        self.assertEqual(response.status_code, 405)

# Create your tests here.
