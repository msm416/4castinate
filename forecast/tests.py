import random
import string

from django.urls import reverse
from django.test import TestCase

from forecast.helperMethods.forecast_utils import remove_order_by_from_filter
from forecast.helperMethods.rest import fetch_filters_and_update_form
from .models import Query, Form, SUCCESS_MESSAGE, Estimation

"""
NOTE: TEST METHODS RUN AGAINST A FAKE DB. DB FLUSHES AFTER EACH INDIVIDUAL TEST IS RAN.
"""

order_by_clause = " order by"


def random_string_with_digits_and_symbols(string_length=10):
    """ Generate a random string of letters, digits and special characters """
    password_characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(password_characters) for _ in range(string_length))


def random_fields_for_estimationInput_model(query):
    wip_lower_bound = random.randint(0, 10000)
    wip_upper_bound = random.randint(wip_lower_bound, 20000)
    throughput_lower_bound = random.randint(1, 10000)
    throughput_upper_bound = random.randint(throughput_lower_bound, 20000)
    wip_filter = random_string_with_digits_and_symbols(100)
    throughput_filter = random_string_with_digits_and_symbols(100)

    split_rate_wip = random.uniform(0, 1)
    split_rate_throughput = random.uniform(0, 1)

    return {'query': query,
            'wip_lower_bound': wip_lower_bound,
            'wip_upper_bound': wip_upper_bound,
            'throughput_lower_bound': throughput_lower_bound,
            'throughput_upper_bound': throughput_upper_bound,
            'wip_filter': wip_filter,
            'throughput_filter': throughput_filter,
            'split_rate_wip': split_rate_wip,
            'split_rate_throughput': split_rate_throughput}


class UnitTests(TestCase):

    def test_form_validity_check(self):
        """
        Valid forms should give SUCCESS_MESSAGE as response
        on both run_estimation() and check_validity() methods
        """
        query = Query.objects.create(name=random_string_with_digits_and_symbols())

        form = Form.objects.create(**random_fields_for_estimationInput_model(query))

        run_estimation_response = query.run_estimation()
        self.assertEqual(run_estimation_response, SUCCESS_MESSAGE)

        check_validity_response = form.check_validity()
        self.assertEqual(run_estimation_response, check_validity_response)

    def test_remove_order_by_from_filter(self):
        """
        Removing "Order by" from a filter that contains it should return the substring preceding the clause.
        Removing "Order by" from a filter that doesn't contain it should return the original filter.
        """

        # Ensure that first_part does not contain order_by clause by chance
        while True:
            first_part = random_string_with_digits_and_symbols()
            if first_part.lower().find(order_by_clause) == -1:
                break

        second_part = random_string_with_digits_and_symbols()

        concatenation = first_part + order_by_clause + second_part

        self.assertEqual(remove_order_by_from_filter(concatenation), first_part)
        self.assertEqual(remove_order_by_from_filter(first_part), first_part)


class HTTPRequests(TestCase):

    def test_fetch_invalid_form_filters(self):
        """
        Invalid throughput/wip filter should return [-1,-1] for low/high throughput/wip.
        """

        # invalidate jql by appending the reserved keyword " ORDER BY " (resulting in incomplete jql)
        throughput_filter = f"{random_string_with_digits_and_symbols()}{order_by_clause}"
        wip_filter = f"{random_string_with_digits_and_symbols()}{order_by_clause}"

        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(**random_fields_for_estimationInput_model(query))
        Form.objects.filter(query=query).update(wip_filter=wip_filter,
                                                throughput_filter=throughput_filter)

        form = Form.objects.get(query=query)
        fetch_filters_and_update_form(form)

        self.assertEqual(form.wip_lower_bound, -1)
        self.assertEqual(form.wip_upper_bound, -1)
        self.assertEqual(form.throughput_lower_bound, -1)
        self.assertEqual(form.throughput_upper_bound, -1)

    def test_fetch_valid_form_wip_filter(self):
        """
        Any valid JQL Query for wip filter will result in some positive wip (>=0)
        Not any valid JQL Query for throughput filter will result in some strictly positive wip (>0)
        One valid JQL Query for wip/throughput is "status = Done"

        """

        wip_filter = throughput_filter = "status = Done"
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(**random_fields_for_estimationInput_model(query))
        Form.objects.filter(query=query).update(
            wip_filter=wip_filter,
            throughput_filter=throughput_filter,
            wip_lower_bound=-1,
            wip_upper_bound=-1)

        form = Form.objects.get(query=query)
        fetch_filters_and_update_form(form)

        self.assertGreaterEqual(form.wip_lower_bound, 0)
        self.assertGreaterEqual(form.wip_upper_bound, 0)


class CallViewsTests(TestCase):

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

        # Post with invalid fields on form won't create an Estimation in the DB
        invalid_fields = random_fields_for_estimationInput_model(query)
        invalid_fields['wip_lower_bound'] = -1

        self.client.post(reverse('forecast:run_estimation',
                                 args=(query.pk,)),
                         invalid_fields)

        self.assertEqual(False, Estimation.objects.exists())

        response = self.client.post(reverse('forecast:run_estimation',
                                            args=(query.pk,)),
                                    random_fields_for_estimationInput_model(query))

        self.assertRedirects(response, reverse('forecast:detail',
                                               args=(query.pk, query.run_estimation())))
        self.assertEqual(True, Estimation.objects.exists())

    def test_valid_get_req_results(self):
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        Form.objects.create(query=query)

        response = query.run_estimation()
        self.assertEqual(response, SUCCESS_MESSAGE)

        estimation = query.estimation_set.order_by('-creation_date').first()
        response = self.client.get(reverse('forecast:results',
                                           args=(query.pk, estimation.pk)))
        self.assertEqual(response.status_code, 200)

    def test_valid_post_req_delete_estimation(self):
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        query.estimation_set.create(**random_fields_for_estimationInput_model(query))
        Form.objects.create(query=query)

        self.assertEqual(True, Estimation.objects.exists())

        response = self.client.post(reverse('forecast:delete_estimation',
                                            args=(query.pk, Estimation.objects.get().pk)),
                                    random_fields_for_estimationInput_model(query))

        self.assertRedirects(response, reverse('forecast:detail',
                                               args=(query.pk,)))

        self.assertEqual(False, Estimation.objects.exists())

    def test_valid_post_req_delete_query(self):
        query = Query.objects.create(name=random_string_with_digits_and_symbols())
        self.assertEqual(True, Query.objects.exists())
        response = self.client.post(reverse('forecast:delete_query',
                                            args=(query.pk,)))

        self.assertRedirects(response, reverse('forecast:index'))

        self.assertEqual(False, Query.objects.exists())
