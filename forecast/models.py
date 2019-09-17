from numpy import random, ceil
import time

from django.db import models
from django.utils import timezone

WEEK_IN_DAYS = 7
SUCCESS_MESSAGE = "succeeded"


class EstimationInput(models.Model):
    creation_date = models.DateTimeField(default=timezone.now)

    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)
    # Default: we consider forms that don't use filter to determine wip
    wip_filter = models.TextField(default="")

    throughput_lower_bound = models.FloatField(default=1.00)
    throughput_upper_bound = models.FloatField(default=5.00)
    # Default: we consider forms that don't use filter to determine throughput
    throughput_filter = models.TextField(default="")

    split_rate_wip = models.FloatField(default=0.5)
    split_rate_throughput = models.FloatField(default=0.7)

    simulation_count = models.PositiveSmallIntegerField(default=10000)

    class Meta:
        abstract = True


class Query(models.Model):
    name = models.CharField(max_length=200)

    description = models.CharField(max_length=200, default='N/A')

    creation_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def run_estimation(self):
        start_time = time.time()

        form = self.form

        run_estimation_response = form.check_validity()

        if run_estimation_response != SUCCESS_MESSAGE:
            return run_estimation_response

        wip = random.uniform(form.wip_lower_bound, form.wip_upper_bound,
                             (form.simulation_count,))

        weekly_throughput = random.uniform(form.throughput_lower_bound, form.throughput_upper_bound,
                                           (form.simulation_count,))

        completion_duration = (ceil(wip / weekly_throughput)).astype(int)

        durations = ';'.join(map(str, completion_duration))
        end_time = time.time()
        msg = f"Elapsed simulation is: {str(end_time - start_time)} seconds."

        # Create new estimation
        self.estimation_set\
            .create(query=self,
                    durations=durations,
                    message=msg,
                    wip_lower_bound=form.wip_lower_bound,
                    wip_upper_bound=form.wip_upper_bound,
                    wip_filter=form.wip_filter,
                    throughput_lower_bound=form.throughput_lower_bound,
                    throughput_upper_bound=form.throughput_upper_bound,
                    throughput_filter=form.throughput_filter,
                    simulation_count=form.simulation_count)
        return run_estimation_response


class Form(EstimationInput):
    query = models.OneToOneField(Query, on_delete=models.CASCADE, primary_key=True)

    def check_validity(self):
        run_estimation_response = ""

        if 0 > self.wip_lower_bound or self.wip_lower_bound > self.wip_upper_bound:
            run_estimation_response += f"WIP is " \
                f"({self.wip_lower_bound}, {self.wip_upper_bound}). "

        if 0 >= self.throughput_lower_bound or self.throughput_lower_bound > self.throughput_upper_bound:
            run_estimation_response += f"Throughput is " \
                f"({self.throughput_lower_bound}, { self.throughput_upper_bound}). "

        if 0 > self.split_rate_wip or self.split_rate_wip > 1.00:
            run_estimation_response += f"Split Rate for WIP is " \
                f"{self.split_rate_wip}. "

        if 0 > self.split_rate_throughput or self.split_rate_throughput > 1.00:
            run_estimation_response += f"Split Rate for Throughput is " \
                f"{self.split_rate_throughput}. "

        return f"failed: {run_estimation_response}" if run_estimation_response else SUCCESS_MESSAGE


class Estimation(EstimationInput):
    query = models.ForeignKey(Query, on_delete=models.CASCADE)

    durations = models.TextField(default='')

    message = models.CharField(max_length=200)

    def __str__(self):
        return self.message
