import datetime
import random
import time
import numpy as np
import matplotlib.pyplot as plt
import mpld3

from django.db import models
from django.utils import timezone


class Team(models.Model):
    description = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date created')

    def __str__(self):
        return self.description

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class Iteration(models.Model):
    # An instance of Iteration could be a sprint
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.description


class ForecastInput(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    forecastinput_text = models.CharField(max_length=200)
    start_date = models.DateField(default=timezone.now())
    wip_lower_bound = models.PositiveSmallIntegerField(default=20)
    wip_upper_bound = models.PositiveSmallIntegerField(default=30)
    split_factor_lower_bound = models.FloatField(default=1.00)
    split_factor_upper_bound = models.FloatField(default=3.00)
    throughput_period_length = models.PositiveSmallIntegerField(default=1)
    throughput_lower_bound = models.PositiveSmallIntegerField(default=1)
    throughput_upper_bound = models.PositiveSmallIntegerField(default=5)
    is_selected = models.BooleanField(default=False)
    nb_of_tests = models.PositiveSmallIntegerField(default=100)

    def __str__(self):
        return self.forecastinput_text

    # t is a team
    # t.forecastinput_set.create(forecastinput_text='Sheet 1',
    # start_date=datetime.date.today(), wip_lower_bound=20,
    # wip_upper_bound=30, split_factor_lower_bound=1.00, split_factor_upper_bound=1.00,
    # throughput_period_length=1, throughput_lower_bound=1, throughput_upper_bound=1)

    def generate_forecast_output(self):
        # This function should run only once per ForecastInput
        if self.forecastoutputsample_set.count() != 0:
            return
        for i in range(self.nb_of_tests):
            start_time = time.time()
            wip = random.uniform(self.wip_lower_bound, self.wip_upper_bound)
            split_rate = random.uniform(self.split_factor_lower_bound, self.split_factor_upper_bound)
            throughput = random.uniform(self.throughput_lower_bound, self.throughput_upper_bound)

            completion_duration = int((wip * split_rate) / throughput)
            end_time = time.time()
            msg = "In " + str(completion_duration) + " weeks we're done for this sprint. #Tasks is: " \
                   + str(wip * split_rate) + " and throughput is: " + str(throughput) + ".\n" \
                   + "Elapsed time was: " + str(end_time - start_time) + "seconds."

            forecastoutputsample = ForecastOutputSample(forecastinput=self,
                                                        completion_duration=completion_duration,
                                                        output_message=msg)
            forecastoutputsample.save()


class ForecastOutputSample(models.Model):
    forecastinput = models.ForeignKey(ForecastInput, on_delete=models.CASCADE)
    completion_duration = models.PositiveSmallIntegerField()
    output_message = models.CharField(max_length=200)

    def __str__(self):
        return self.output_message
