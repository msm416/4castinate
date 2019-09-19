from numpy import random, ceil

from django.db import models
from django.utils import timezone

from forecast.helperMethods.forecast_utils import parse_durations_for_ui, list_of_primitives_as_string

WEEK_IN_DAYS = 7
SUCCESS_MESSAGE = "succeeded"


class EstimationInput(models.Model):
    creation_date = models.DateTimeField(default=timezone.now)

    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)

    wip_filter = models.TextField(default="")

    throughput_lower_bound = models.FloatField(default=1.00)
    throughput_upper_bound = models.FloatField(default=5.00)

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
        form = self.form

        run_estimation_response = form.check_validity()

        if run_estimation_response != SUCCESS_MESSAGE:
            return run_estimation_response

        wip = random.uniform(form.wip_lower_bound, form.wip_upper_bound,
                             (form.simulation_count,))

        weekly_throughput = random.uniform(form.throughput_lower_bound, form.throughput_upper_bound,
                                           (form.simulation_count,))

        completion_duration = (ceil(wip / weekly_throughput)).astype(int)

        durations = list_of_primitives_as_string(completion_duration)

        centile_values, weeks, weeks_frequency, point_radius_list, point_color_list \
            = parse_durations_for_ui(completion_duration)

        # Create new Estimation
        self.estimation_set\
            .create(query=self,
                    durations=durations,
                    wip_lower_bound=form.wip_lower_bound,
                    wip_upper_bound=form.wip_upper_bound,
                    wip_filter=form.wip_filter,
                    throughput_lower_bound=form.throughput_lower_bound,
                    throughput_upper_bound=form.throughput_upper_bound,
                    throughput_filter=form.throughput_filter,
                    simulation_count=form.simulation_count,
                    centile_values=list_of_primitives_as_string(centile_values),
                    weeks=list_of_primitives_as_string(weeks),
                    weeks_frequency=list_of_primitives_as_string(weeks_frequency),
                    point_radius_list=list_of_primitives_as_string(point_radius_list),
                    point_color_list=list_of_primitives_as_string(point_color_list))

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

    durations = models.TextField()

    centile_values = models.TextField()
    weeks = models.TextField()
    weeks_frequency = models.TextField()
    point_radius_list = models.TextField()
    point_color_list = models.TextField()

