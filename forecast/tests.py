from datetime import timedelta

from django.utils import timezone
from django.urls import reverse
from django.test import TestCase

from .models import Board


def create_board(name, days):
    """
    Create a board with the given `name` and published the
    given number of `days` offset to now (negative for boards published
    in the past, positive for boards that have yet to be published).
    """
    time = timezone.now() + timedelta(days=days)
    return Board.objects.create(name=name, creation_date=time)


class BoardModelTests(TestCase):

    def test_was_published_recently_with_future_board(self):
        """
        was_published_recently() returns False for board whose creation_date
        is in the future.
        """
        future_time = timezone.now() + timedelta(days=30)
        future_board = Board(creation_date=future_time)
        self.assertIs(future_board.was_published_recently(), False)

    def test_was_published_recently_with_old_board(self):
        """
        was_published_recently() returns False for boards whose creation_date
        is older than 1 day.
        """
        old_time = timezone.now() - timedelta(days=1, seconds=1)
        old_board = Board(creation_date=old_time)
        self.assertIs(old_board.was_published_recently(), False)

    def test_was_published_recently_with_recent_board(self):
        """
        was_published_recently() returns True for boards whose creation_date
        is within the last day.
        """
        recent_time = timezone.now() - timedelta(hours=23, minutes=59, seconds=59)
        recent_board = Board(creation_date=recent_time)
        self.assertIs(recent_board.was_published_recently(), True)


class BoardIndexViewTests(TestCase):
    def test_no_boards(self):
        """
        If no boards exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total number of boards in database: 0")
        self.assertQuerysetEqual(response.context['latest_board_list'], [])

    def test_past_board(self):
        """
        Boards with a creation_date in the past are displayed on the
        index page.
        """
        create_board(name="Past board.", days=-30)
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['latest_board_list'],
            ['<Board: Past board.>']
        )

    def test_future_board(self):
        """
        Boards with a creation_date in the future aren't displayed on
        the index page.
        """
        create_board(name="Future board.", days=30)
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total number of boards in database: 0")
        self.assertQuerysetEqual(response.context['latest_board_list'], [])

    def test_future_board_and_past_board(self):
        """
        Even if both past and future boards exist, only past boards
        are displayed.
        """
        create_board(name="Past board.", days=-30)
        create_board(name="Future board.", days=30)
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['latest_board_list'],
            ['<Board: Past board.>']
        )

    def test_two_past_boards(self):
        """
        The boards index page may display multiple boards.
        """
        create_board(name="Past board 1.", days=-30)
        create_board(name="Past board 2.", days=-5)
        response = self.client.get(reverse('forecast:index'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['latest_board_list'],
            ['<Board: Past board 2.>', '<Board: Past board 1.>']
        )
