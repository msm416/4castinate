from datetime import datetime
from numpy import random
import time

from django.db import models
from django.utils import timezone

WEEK_IN_DAYS = 7
LONG_TIME_AGO = "1011-12-13"


class Board(models.Model):
    name = models.CharField(max_length=200)
    data_sources = models.CharField(max_length=200, default='None')
    project_name = models.CharField(max_length=200, default='None')
    board_type = models.CharField(max_length=200, default='Hybrid')
    creation_date = models.DateTimeField(default=timezone.now)
    fetch_date = models.DateTimeField(null=True)
    source_id = models.CharField(max_length=200, default='None')

    def __str__(self):
        return self.name


class Issue(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, default="some issue")
    state = models.CharField(max_length=200, default='Done')
    issue_type = models.CharField(max_length=200, default='non-epic')
    epic_parent = models.CharField(max_length=200, default='None')
    source = models.CharField(max_length=200, default='None')
    source_id = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class Iteration(models.Model):
    # An instance of Iteration could be a sprint
    # source = Jira / Trello / None
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
    duration = models.PositiveSmallIntegerField(default=WEEK_IN_DAYS)
    throughput = models.PositiveSmallIntegerField(default=3)

    # Default: Iteration does not come from some external source
    source = models.CharField(max_length=200, default='None')
    state = models.CharField(max_length=200, default='INVALID_STATE')

    # Id of Iteration on JIRA (Unique for boards)
    source_id = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class Form(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    creation_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=datetime.strptime(LONG_TIME_AGO, "%Y-%m-%d"))

    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)

    # Default: we consider forms that don't use historical wip data
    wip_from_data = models.BooleanField(default=False)

    split_factor_lower_bound = models.FloatField(default=1.00)
    split_factor_upper_bound = models.FloatField(default=3.00)

    throughput_lower_bound = models.FloatField(default=1.00)
    throughput_upper_bound = models.FloatField(default=5.00)

    # Default: we consider forms that don't use historical throughput data
    throughput_from_data = models.BooleanField(default=False)

    # PK of Iteration object that represents the start point (we consider
    # Iteration objects until the most recent Iteration - i.e. present)
    throughput_from_data_start_date = models.DateField(default=timezone.now)
    simulation_count = models.PositiveSmallIntegerField(default=1000)

    is_selected = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    # Returns always >= 0
    # TODO: implement this for forms that represent epics
    def get_wip_from_data(self, epic_parent):
        return Issue.objects\
            .filter(board__name=self.board.name,
                    state='Ongoing',
                    epic_parent=epic_parent)\
            .count()

    # Returns always >= 0
    # Returns the average weekly throughput
    def get_throughput_rate_avg(self):
        cnt = 0
        throughput = 0
        for iteration in self.board\
                             .iteration_set\
                             .filter(state='closed',
                                     start_date__gte=self.start_date)\
                             .all():
            if iteration.throughput == 0 or iteration.duration == 0:
                continue

            throughput += (iteration.throughput * WEEK_IN_DAYS / iteration.duration)
            cnt += 1
        return 0 if cnt == 0 else throughput/cnt

    # One test => One Simulation instance is created.
    # Each form has at most one Simulation. Subsequent calls will overwrite the Simulation
    # for data forms, and will return the same simulation for non-data forms.
    def gen_simulations(self):

        if self.throughput_from_data:
            throughput_rate_avg = self.get_throughput_rate_avg()
            # TODO: figure how to avoid recomputing simulation (but NOT 'if th_l_b == g_th_avg()')
            self.throughput_lower_bound = throughput_rate_avg
            self.throughput_upper_bound = throughput_rate_avg
            self.save()
        # else:
        #     if self.simulation_set.exists():
        #         return

        # if self.wip_from_data:
        #     wip = self.get_wip_from_data()

        start_time = time.time()

        wip = random.uniform(self.wip_lower_bound, self.wip_upper_bound,
                             (self.simulation_count,))
        split_rate = random.uniform(self.split_factor_lower_bound, self.split_factor_upper_bound,
                                    (self.simulation_count,))
        weekly_throughput = random.uniform(self.throughput_lower_bound, self.throughput_upper_bound,
                                           (self.simulation_count,))
        completion_duration = ((wip * split_rate) / weekly_throughput).astype(int)
        durations = ';'.join(map(str, completion_duration))

        end_time = time.time()
        msg = f"Elapsed time is: {str(end_time - start_time)} seconds."

        # Delete previous Simulation (if it exists)
        # TODO: ONE TO ONE FORM-SIMULATION
        self.simulation_set.all().delete()

        # Create new Simulation
        self.simulation_set.create(form=self, message=msg, durations=durations)


class Simulation(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    durations = models.TextField(default='')
    message = models.CharField(max_length=200)

    def __str__(self):
        return self.message


class MsgLogWebhook(models.Model):
    text = models.TextField(default='abcdefgh')
    msglog_id = models.PositiveSmallIntegerField(default=1)
    cnt = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.text

