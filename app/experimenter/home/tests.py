from django.test import TestCase
from django.core.urlresolvers import reverse


class CounterTest(TestCase):

    def test_counter_returns_value(self):
        response = self.client.get(reverse('home-landing'))
        self.assertTrue(response.status_code, 200)
