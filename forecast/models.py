from numpy import random, ceil
import time

from django.db import models
from django.utils import timezone

WEEK_IN_DAYS = 7


class Query(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, default='N/A')
    creation_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def create_simulation(self):
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


class Form(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    creation_date = models.DateTimeField(default=timezone.now)

    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)
    # Default: we consider forms that don't use filter to determine wip
    wip_filter = models.TextField(default="")

    throughput_lower_bound = models.FloatField(default=1.00)
    throughput_upper_bound = models.FloatField(default=5.00)
    # Default: we consider forms that don't use filter to determine throughput
    throughput_filter = models.TextField(default="")

    split_factor_lower_bound = models.FloatField(default=1.00)
    split_factor_upper_bound = models.FloatField(default=3.00)

    simulation_count = models.PositiveSmallIntegerField(default=1000)

    is_selected = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Simulation(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    durations = models.TextField(default='')
    message = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message
