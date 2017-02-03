from django.test import TestCase
from .management.commands.utils import new_get_plexts
# Create your tests here.

class SpiderTestCase(TestCase):
    def test_can_get_plext(self):
        response = new_get_plexts()
        self.assertEqual(response.status_code,200)
