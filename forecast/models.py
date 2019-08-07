from datetime import datetime, timedelta
import random
import time

from django.db import models
from django.utils import timezone

WEEK_IN_DAYS = 7
LONG_TIME_AGO = "1011-12-13"


class Board(models.Model):
    description = models.CharField(max_length=200)
    data_sources = models.CharField(max_length=200, default='None')
    project_name = models.CharField(max_length=200, default='None')
    board_type = models.CharField(max_length=200, default='Hybrid')
    creation_date = models.DateTimeField(default=timezone.now)
    fetch_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.description

    def was_published_recently(self):
        return self.creation_date >= timezone.now() - timedelta(days=1)


class Iteration(models.Model):
    # An instance of Iteration could be a sprint
    # Default duration = 1 week (7days)
    # source = Jira / Trello / None
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
    duration = models.PositiveSmallIntegerField(default=WEEK_IN_DAYS)

    # Default: Iteration does not come from some external source
    source = models.CharField(max_length=200, default='None')
    throughput = models.PositiveSmallIntegerField(default=3)

    def __str__(self):
        return self.description


class Form(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=datetime.strptime(LONG_TIME_AGO, "%Y-%m-%d"))
    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)
    split_factor_lower_bound = models.FloatField(default=1.00)
    split_factor_upper_bound = models.FloatField(default=3.00)

    # TODO: CLEAN FORM
    # Default: all sprints are of 1 week
    throughput_period_length = models.PositiveSmallIntegerField(default=1)

    throughput_lower_bound = models.FloatField(default=1.00)
    throughput_upper_bound = models.FloatField(default=5.00)

    # Default: we consider forms that don't use historical data
    throughput_from_data = models.BooleanField(default=False)

    # PK of Iteration object that represents the start point (we consider
    # Iteration objects until the most recent Iteration - i.e. present)
    throughput_from_data_start_date = models.DateField(default=timezone.now)
    simulation_count = models.PositiveSmallIntegerField(default=100)

    def __str__(self):
        return self.description

    def get_throughput_avg(self):
        cnt = 0
        throughput = 0
        for iteration in self.board.iteration_set.all():
            if self.start_date <= iteration.start_date:
                throughput += (iteration.throughput * WEEK_IN_DAYS / iteration.duration)
                cnt += 1
        return -1 if cnt == 0 else throughput/cnt

    # One test => One Simulation instance is created
    def gen_simulations(self):
        # TODO: Recompute this in data forms
        # Run only once per Form

        throughput_avg = self.get_throughput_avg()

        if self.throughput_from_data:
            if self.throughput_lower_bound == throughput_avg:
                return
            else:
                self.throughput_lower_bound = throughput_avg
                self.throughput_upper_bound = throughput_avg
                self.save()
        else:
            if self.simulation_set.exists():
                return

        durations = ""
        start_time = time.time()
        for i in range(self.simulation_count):
            wip = random.uniform(self.wip_lower_bound, self.wip_upper_bound)
            split_rate = random.uniform(self.split_factor_lower_bound, self.split_factor_upper_bound)
            weekly_throughput = random.uniform(self.throughput_lower_bound, self.throughput_upper_bound)

            completion_duration = int((wip * split_rate) / weekly_throughput)
            if i == 0:
                durations = str(completion_duration)
            else:
                durations = ';'.join([durations, str(completion_duration)])

        end_time = time.time()
        msg = f"Elapsed time is: {str(end_time - start_time)} seconds."

        # Delete previous Simulation (if it exists)
        # TODO: ONE TO ONE FORM-SIMULATION
        self.simulation_set.all().delete()

        # Create new Simulation
        self.simulation_set.create(form=self, message=msg, durations=durations)


class Simulation(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    durations = models.TextField(null=True)
    message = models.CharField(max_length=200)

    def __str__(self):
        return self.message
