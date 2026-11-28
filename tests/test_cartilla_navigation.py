import unittest
from unittest.mock import patch

import app as app_module


class CartillaNavigationTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config['TESTING'] = True

    def test_dashboard_groups_indicators_and_keeps_charts_on_separate_pages(self):
        with patch('app.get_db_or_fallback', return_value=None):
            with app_module.app.test_client() as client:
                with client.session_transaction() as session:
                    session['usuario'] = 'Milena'
                    session['rol'] = 'administrador'
                response = client.get('/dashboard')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count(b'data-cartilla-page'), 4)
        self.assertIn(b'data-cartilla-label="Indicadores principales"', response.data)
        self.assertEqual(response.data.count(b'class="kpi-card'), 4)
        self.assertIn(b'/static/js/cartilla.js', response.data)

    def test_associate_form_keeps_all_fields_in_one_cartilla_page(self):
        with patch('app.get_db_or_fallback', return_value=None):
            with app_module.app.test_client() as client:
                with client.session_transaction() as session:
                    session['usuario'] = 'Milena'
                    session['rol'] = 'administrador'
                response = client.get('/nuevo-asociado')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-cartilla', response.data)
        self.assertIn(b'name="nombre"', response.data)
        self.assertIn(b'name="frecuencia_pago"', response.data)
        self.assertIn(b'name="viviendas[]"', response.data)
        self.assertNotIn(b'data-cartilla-page', response.data)

    def test_pqr_form_keeps_all_fields_in_one_cartilla_page(self):
        with app_module.app.test_client() as client:
            with client.session_transaction() as session:
                session['usuario'] = 'Ana Torres'
                session['rol'] = 'usuario'
                session['documento'] = '123456789'
            response = client.get('/radicar-pqr')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-cartilla', response.data)
        self.assertIn(b'name="tipo"', response.data)
        self.assertIn(b'name="asunto"', response.data)
        self.assertNotIn(b'data-cartilla-page', response.data)


if __name__ == '__main__':
    unittest.main()
