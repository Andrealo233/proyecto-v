import unittest
from unittest.mock import patch

import app as app_module
from app import calculate_account_summary, parse_viviendas


class BillingCalculationTests(unittest.TestCase):
    def test_monthly_total_multiplies_tariff_by_houses(self):
        summary = calculate_account_summary(15000, 'Mensual', ['Casa 1', 'Casa 2', 'Casa 3'], [])

        self.assertEqual(summary['valor_por_vivienda'], 15000)
        self.assertEqual(summary['total'], 45000)

    def test_quincenal_total_includes_recurring_charges(self):
        charges = [{'valor': 2000}, {'valor': 1000}]
        summary = calculate_account_summary(15000, 'Quincenal', ['Casa 1', 'Casa 2'], charges)

        self.assertEqual(summary['valor_por_vivienda'], 7500)
        self.assertEqual(summary['valor_cargos'], 3000)
        self.assertEqual(summary['total'], 18000)

    def test_missing_houses_are_not_charged_for_base_tariff(self):
        summary = calculate_account_summary(15000, 'Mensual', [], [])

        self.assertEqual(summary['cantidad_viviendas'], 0)
        self.assertEqual(summary['total'], 0)

    def test_monthly_tariff_must_be_even_for_exact_quincenal_amount(self):
        with self.assertRaises(ValueError):
            calculate_account_summary(15001, 'Quincenal', ['Casa 1'], [])


class ViviendaValidationTests(unittest.TestCase):
    def test_parse_viviendas_trims_and_ignores_blank_lines(self):
        self.assertEqual(parse_viviendas([' Casa principal ', '', 'Lote 2'], required=True),
                         ['Casa principal', 'Lote 2'])

    def test_parse_viviendas_rejects_duplicate_names(self):
        with self.assertRaises(ValueError):
            parse_viviendas(['Casa principal', ' casa principal '])

    def test_new_associate_requires_at_least_one_vivienda(self):
        with self.assertRaises(ValueError):
            parse_viviendas(['', '  '], required=True)


class BillingAccountRouteTests(unittest.TestCase):
    def test_associate_sees_house_details_and_monthly_total(self):
        demo_associate = {
            'id': 42,
            'nombre': 'Ana Torres',
            'documento': '123456789',
            'telefono': '',
            'vereda': '',
            'estado': 'Activo',
            'frecuencia_pago': 'Mensual',
            'viviendas': ['Casa 1', 'Casa 2', 'Casa 3'],
        }
        app_module.app.config['TESTING'] = True
        with patch('app.get_db_or_fallback', return_value=None), \
                patch('app.DEMO_USUARIOS', [demo_associate]):
            with app_module.app.test_client() as client:
                with client.session_transaction() as session:
                    session['usuario'] = demo_associate['nombre']
                    session['rol'] = 'usuario'
                    session['documento'] = demo_associate['documento']
                response = client.get('/mi-cuenta')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Casa 3', response.data)
        self.assertIn(b'45.000', response.data)


if __name__ == '__main__':
    unittest.main()
