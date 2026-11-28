import unittest
from unittest.mock import patch

import app as app_module


class PublicationBookTests(unittest.TestCase):
    def test_homepage_renders_one_page_per_publication_with_controls(self):
        publications = [
            {'id': 1, 'titulo': 'Aviso uno', 'contenido': 'Contenido uno', 'activo': 1, 'actualizado_en': ''},
            {'id': 2, 'titulo': 'Aviso dos', 'contenido': 'Contenido dos', 'activo': 1, 'actualizado_en': ''},
        ]
        with patch('app.get_db', return_value=None), patch('app.DEMO_PUBLICACIONES', publications):
            response = app_module.app.test_client().get('/')

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Aviso uno', html)
        self.assertIn('<article data-book-page hidden>', html)
        self.assertIn('class="book-tab book-tab-next" data-book-next', html)
        self.assertIn('Página 1 de 2', html)

    def test_empty_publication_book_shows_placeholder_without_page_controls(self):
        with patch('app.get_db', return_value=None), patch('app.DEMO_PUBLICACIONES', []):
            response = app_module.app.test_client().get('/')

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Este libro espera sus primeros avisos', html)
        self.assertIn('Sin publicaciones', html)
        self.assertIn('Página 1 de 1', html)
        self.assertNotIn('class="book-tab book-tab-next"', html)


if __name__ == '__main__':
    unittest.main()
