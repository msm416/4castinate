from datetime import timedelta
import time
import random
import string

from django.utils import timezone
from django.urls import reverse
from django.test import TestCase
from django.db.models import Sum

from .models import Query, Form, Estimation, SUCCESS_MESSAGE


"""
NOTE: TEST METHODS RUN AGAINST A FAKE DB. DB FLUSHES AFTER EACH METHOD.
"""


def random_string_with_digits_and_symbols(string_length=10):
    """ Generate a random string of letters, digits and special characters """
    password_characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(password_characters) for _ in range(string_length))


class SimulationTests(TestCase):
    def test_run_estimation_on_query_with_valid_form(self):
        """
        Invalid forms should not create Estimation models and save them db.

        run_estimation should give back corresponding message.
        """

        query = Query.objects.create(name="query")

        wip_lower_bound = random.randint(0, 10000)
        wip_upper_bound = random.randint(0, 20000)
        throughput_lower_bound = random.randint(0, 10000)
        throughput_upper_bound = random.randint(throughput_lower_bound, 20000)
        name = random_string_with_digits_and_symbols(100)
        wip_filter = random_string_with_digits_and_symbols(100)
        throughput_filter = random_string_with_digits_and_symbols(100)
        split_factor_lower_bound = random.randint(1, 10000)
        split_factor_upper_bound = random.randint(split_factor_lower_bound, 20000)

        _ = \
            Form.objects.create(query=query,
                                name=name,
                                wip_lower_bound=wip_lower_bound,
                                wip_upper_bound=wip_upper_bound,
                                throughput_lower_bound=throughput_lower_bound,
                                throughput_upper_bound=throughput_upper_bound,
                                wip_filter=wip_filter,
                                throughput_filter=throughput_filter,
                                split_factor_lower_bound=split_factor_lower_bound,
                                split_factor_upper_bound=split_factor_upper_bound)

        response = query.run_estimation()
        self.assertEqual(response, SUCCESS_MESSAGE)


# class FormModelTests(TestCase):
#     def create_iterations(self, board, nb_of_iter, state, now):
#         for i in range(1, nb_of_iter + 1):
#             board.iteration_set.create(start_date=(now - timedelta(seconds=i)), throughput=i, state=state)
#             board.iteration_set.create(start_date=(now + timedelta(seconds=i)), throughput=i, state=state)
#
#
# class BoardIndexViewTests(TestCase):
#     def test_no_boards(self):
#         """
#         If no boards exist, an appropriate message is displayed.
#         """
#         response = self.client.get(reverse('forecast:index'))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "Total number of boards in database: 0")
#         self.assertQuerysetEqual(response.context['latest_board_list'], [])
#
#     def test_future_board_past_board_and_past_recent_board(self):
#         """
#         Even if both past and future boards exist, only past boards are displayed.
#         """
#         now = timezone.now()
#         month_offset = timedelta(days=30)
#         Board.objects.create(name="Past board.",
#                              creation_date=(now - month_offset))
#         Board.objects.create(name="Past recent board.",
#                              creation_date=now)
#         Board.objects.create(name="Future board.",
#                              creation_date=(now + month_offset))
#         response = self.client.get(reverse('forecast:index'))
#         self.assertEqual(response.status_code, 200)
#         self.assertQuerysetEqual(
#             response.context['latest_board_list'],
#             ['<Board: Past recent board.>', '<Board: Past board.>'])


# class JiraAPITests(TestCase):
    # def test_jira_get_data_and_populate_db(self):
    #     """
    #     Fetching is deterministic (and we allow multiple fetches).
    #
    #     All 'Done' Issues (That aren't EPIC type) are assigned to some Iteration.
    #     """
    #     self.assertEqual(jira_get_boards(), 200)
    #     first_fetch_nb_iterations = Iteration.objects.all().count()
    #     first_fetch_nb_issues = Issue.objects.all().count()
    #
    #     self.assertEqual(Issue.objects.filter(state='Done')
    #                                   .exclude(issue_type='Epic').count(),
    #                      Iteration.objects.all()
    #                                       .aggregate(Sum('throughput'))['throughput__sum'])
    #
    #     self.assertEqual(jira_get_boards(), 200)
    #     second_fetch_nb_iterations = Iteration.objects.all().count()
    #     second_fetch_nb_issues = Issue.objects.all().count()
    #
    #     self.assertEqual((first_fetch_nb_iterations, first_fetch_nb_issues),
    #                      (second_fetch_nb_iterations, second_fetch_nb_issues))
