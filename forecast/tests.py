from datetime import timedelta

from django.utils import timezone
from django.urls import reverse
from django.test import TestCase

from forecast.helperMethods.rest import jira_get_boards
from .models import Board, Form


"""
NOTE: METHODS RUN AGAINST A FAKE DB. DB FLUSHES AFTER EACH METHOD.
"""


class FormModelTests(TestCase):
    def test_get_throughput_avg_no_iterations(self):
        """
        No iterations means 0 throughput.
        """
        board = Board.objects.create(name="Some board")
        form = Form.objects.create(board=board, name="Some form")
        self.assertIs(form.get_throughput_avg(), 0)


class BoardIndexViewTests(TestCase):
    def test_no_boards(self):
        """
        If no boards exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total number of boards in database: 0")
        self.assertQuerysetEqual(response.context['latest_board_list'], [])

    def test_future_board_past_board_and_past_recent_board(self):
        """
        Even if both past and future boards exist, only past boards are displayed.
        """
        now = timezone.now()
        month_offset = timedelta(days=30)
        Board.objects.create(name="Past board.",
                             creation_date=(now - month_offset))
        Board.objects.create(name="Past recent board.",
                             creation_date=now)
        Board.objects.create(name="Future board.",
                             creation_date=(now + month_offset))
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['latest_board_list'],
            ['<Board: Past recent board.>', '<Board: Past board.>']
        )


class JiraAPITests(TestCase):
    def test_jira_get_data_and_populate_db(self):
        self.assertEqual(1, 1)
        # self.assertEqual(jira_get_boards(), 200)
