from datetime import timedelta
import time
import random
import string

from django.utils import timezone
from django.urls import reverse
from django.test import TestCase
from django.db.models import Sum

from forecast.helperMethods.rest import fetch_filters_and_update_form
from .models import Query, Form, Estimation, SUCCESS_MESSAGE


"""
NOTE: TEST METHODS RUN AGAINST A FAKE DB. DB FLUSHES AFTER EACH METHOD.
"""


def random_string_with_digits_and_symbols(string_length=10):
    """ Generate a random string of letters, digits and special characters """
    password_characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(password_characters) for _ in range(string_length))


def random_fields_for_form_model(query):
    wip_lower_bound = random.randint(0, 10000)
    wip_upper_bound = random.randint(wip_lower_bound, 20000)
    throughput_lower_bound = random.randint(0, 10000)
    throughput_upper_bound = random.randint(throughput_lower_bound, 20000)
    wip_filter = random_string_with_digits_and_symbols(100)
    throughput_filter = random_string_with_digits_and_symbols(100)

    split_factor_lower_bound = random.uniform(1, 10000)
    split_factor_upper_bound = random.uniform(split_factor_lower_bound, 20000)

    return {'query': query,
            'wip_lower_bound': wip_lower_bound,
            'wip_upper_bound': wip_upper_bound,
            'throughput_lower_bound': throughput_lower_bound,
            'throughput_upper_bound': throughput_upper_bound,
            'wip_filter': wip_filter,
            'throughput_filter': throughput_filter,
            'split_factor_lower_bound': split_factor_lower_bound,
            'split_factor_upper_bound': split_factor_upper_bound}


class UnitTests(TestCase):

    def test_form_validity_check(self):
        """
        Valid forms should give SUCCESS_MESSAGE as response
        on both run_estimation() and check_validity() methods
        """
        for _ in range(0, 20):
            query = Query.objects.create(name=random_string_with_digits_and_symbols())

            form = Form.objects.create(**random_fields_for_form_model(query))

            run_estimation_response = query.run_estimation()
            self.assertEqual(run_estimation_response, SUCCESS_MESSAGE)

            check_validity_response = form.check_validity()
            self.assertEqual(run_estimation_response, check_validity_response)

    def test_invalid_form_filters(self):
        """
        Invalid throughput/wip filter should return [-1,-1] for low/high throughput/wip.
        """

        # throughput_filter will never match a valid JQL with " ORDER BY "
        throughput_filter = f"{random_string_with_digits_and_symbols()} ORDER BY "
        wip_filter = f"{random_string_with_digits_and_symbols()} ORDER BY "
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(**random_fields_for_form_model(query))
        Form.objects.filter(query=query).update(wip_filter=wip_filter,
                                                throughput_filter=throughput_filter)

        form = Form.objects.get(query=query)
        fetch_filters_and_update_form(form)

        self.assertEqual(form.wip_lower_bound, -1)
        self.assertEqual(form.wip_upper_bound, -1)
        self.assertEqual(form.throughput_lower_bound, -1)
        self.assertEqual(form.throughput_upper_bound, -1)

    def test_valid_form_wip_filter(self):
        """
        ANY VALID JQL QUERY FOR WIP FILTER WILL RESULT IN SOME POSITIVE WIP (>=0)

        TO GENERATE A VALID JQL QUERY, WE"LL CONSIDER THE EMPTY QUERY (i.e. all issues)
        """
        wip_filter = "status = Done"
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(**random_fields_for_form_model(query))
        Form.objects.filter(query=query).update(wip_filter=wip_filter)

        form = Form.objects.get(query=query)
        fetch_filters_and_update_form(form)

        self.assertGreaterEqual(form.wip_lower_bound, 0)
        self.assertGreaterEqual(form.wip_upper_bound, 0)


class ViewTests(TestCase):

    def test_valid_get_req_index(self):
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)

    def test_valid_get_req_detail(self):
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(query=query)

        response = self.client.get(reverse('forecast:detail',
                                           args=(query.pk,
                                                 SUCCESS_MESSAGE)))
        self.assertEqual(response.status_code, 200)

    def test_valid_post_req_create_query(self):
        response = self.client.post(reverse('forecast:create_query'),
                                    {'name': random_string_with_digits_and_symbols(),
                                     'description': random_string_with_digits_and_symbols(),
                                     'filter': random_string_with_digits_and_symbols()})
        self.assertRedirects(response, reverse('forecast:index'))

    def test_valid_post_req_run_estimation(self):
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(query=query)

        response = self.client.post(reverse('forecast:run_estimation',
                                            args=(query.pk,)),
                                    random_fields_for_form_model(query))
        self.assertRedirects(response, reverse('forecast:detail',
                                               args=(query.pk, query.run_estimation())))

    def test_valid_get_req_results(self):
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(query=query)

        response = query.run_estimation()
        self.assertEqual(response, SUCCESS_MESSAGE)

        estimation = query.estimation_set.order_by('-creation_date').first()
        response = self.client.get(reverse('forecast:results',
                                           args=(query.pk, estimation.pk)))
        self.assertEqual(response.status_code, 200)
