from datetime import datetime
from numpy import random, ceil
import time

from django.db import models
from django.utils import timezone

from forecast.helperMethods.utils import parse_filter

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


class Query(models.Model):
    name = models.CharField(max_length=200)
    data_sources = models.CharField(max_length=200, default='Jira')

    def __str__(self):
        return self.name

    def gen_simulations(self):
        start_time = time.time()

        form = self.form_set.get()

        wip = random.uniform(form.wip_lower_bound, form.wip_upper_bound,
                             (form.simulation_count,))
        split_rate = random.uniform(form.split_factor_lower_bound, form.split_factor_upper_bound,
                                    (form.simulation_count,))
        weekly_throughput = random.uniform(form.throughput_lower_bound, form.throughput_upper_bound,
                                           (form.simulation_count,))
        completion_duration = (ceil((wip * split_rate) / weekly_throughput)).astype(int)
        durations = ';'.join(map(str, completion_duration))

        end_time = time.time()
        msg = f"Elapsed time is: {str(end_time - start_time)} seconds."

        # Create new Simulation
        self.simulation_set.create(query=form, message=msg, durations=durations)


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
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    creation_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=datetime.strptime(LONG_TIME_AGO, "%Y-%m-%d"))

    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)

    # Default: we consider forms that don't use historical wip data
    wip_from_data = models.BooleanField(default=False)
    wip_from_data_filter = models.TextField(default="")

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
    def get_wip_from_data(self):
        print(f"WE COMPUTING WIP: - {self.name} filter: {self.wip_from_data_filter}")
        q_filter = parse_filter(self.wip_from_data_filter, self.wip_from_data)
        return Issue.objects\
            .filter(board__name=self.board.name,
                    state='Ongoing')\
            .exclude(issue_type='Epic')\
            .filter(q_filter)\
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


class Simulation(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    durations = models.TextField(default='')
    message = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message


class MsgLogWebhook(models.Model):
    text = models.TextField(default='abcdefgh')
    msglog_id = models.PositiveSmallIntegerField(default=1)
    cnt = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.text
