import datetime

from django.db import models
from django.utils import timezone


class Team(models.Model):
    team_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date created')

    def __str__(self):
        return self.team_text

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class TeamData(models.Model):
    # An instance of TeamData could be a sprint
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    teamdata_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    # TODO: remove votes

    def __str__(self):
        return self.teamdata_text


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

    def __str__(self):
        return self.forecast_text

    # t is a team
    # t.forecastinput_set.create(forecastinput_text='Sheet 1',
    # start_date=datetime.date.today(), wip_lower_bound=20,
    # wip_upper_bound=30, split_factor_lower_bound=1.00, split_factor_upper_bound=1.00,
    # throughput_period_length=1, throughput_lower_bound=1, throughput_upper_bound=1)

    def generate_forecast_output(self):
        return "in 10 days we're done for " + self.forecast_text
