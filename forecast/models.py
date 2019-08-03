import datetime
import random
import time
import numpy as np
import matplotlib.pyplot as plt
import mpld3

from django.db import models
from django.utils import timezone


class Board(models.Model):
    description = models.CharField(max_length=200)
    data_sources = models.CharField(max_length=200, default='None')
    project_name = models.CharField(max_length=200, default='None')
    board_type = models.CharField(max_length=200, default='Hybrid')
    pub_date = models.DateTimeField('date created')

    def __str__(self):
        return self.description

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class Iteration(models.Model):
    # An instance of Iteration could be a sprint
    # duration = 1 week
    # source = Jira / Trello / None
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    start_date = models.DateField(default=timezone.now)

    # Default: Iteration does not come from some external source
    source = models.CharField(max_length=200, default='None')
    throughput = models.PositiveSmallIntegerField(default=3)

    def __str__(self):
        return self.description


class Form(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    start_date = models.DateField(default=timezone.now)
    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)
    split_factor_lower_bound = models.FloatField(default=1.00)
    split_factor_upper_bound = models.FloatField(default=3.00)

    # Default: all sprints are of 1 week
    throughput_period_length = models.PositiveSmallIntegerField(default=1)

    throughput_lower_bound = models.PositiveSmallIntegerField(default=1)
    throughput_upper_bound = models.PositiveSmallIntegerField(default=5)

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
            # We're keeping track of the iterations that are not just a couple
            # days after the form's start date (cause we don't want partial iterations)
            if self.start_date - iteration.start_date >= datetime.timedelta(days=7):
                throughput += iteration.throughput
                cnt += 1
        return -1 if cnt == 0 else throughput/cnt

    # One test => One Simulation instance is created
    def gen_simulations(self):
        # TODO: Recompute this in data forms
        # Run only once per Form
        if self.simulation_set.count() != 0:
            return
        for i in range(self.simulation_count):
            start_time = time.time()
            wip = random.uniform(self.wip_lower_bound, self.wip_upper_bound)
            split_rate = random.uniform(self.split_factor_lower_bound, self.split_factor_upper_bound)
            throughput = (self.get_throughput_avg() if self.throughput_from_data
                          else random.uniform(self.throughput_lower_bound, self.throughput_upper_bound))

            completion_duration = int((wip * split_rate) / throughput)
            end_time = time.time()
            msg = "In " + str(completion_duration) + " weeks we're done for this sprint. #Tasks is: " \
                  + str(wip * split_rate) + " and throughput is: " + str(throughput) + ".\n" \
                  + "Elapsed time was: " + str(end_time - start_time) + "seconds."

            simulation = Simulation(form=self, completion_duration=completion_duration, message=msg)
            simulation.save()
            # TODO: Should we save a thing in the DB for each iteration???
            # TODO: NOW THROUGHPUT IS CONSTANT WHEN DATA INVOLVED. DO WE WANT THAT?


class Simulation(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    completion_duration = models.PositiveSmallIntegerField()
    message = models.CharField(max_length=200)

    def __str__(self):
        return self.message
