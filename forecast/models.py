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

    def __str__(self):
        return self.teamdata_text


class ForecastInput(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    forecast_text = models.CharField(max_length=200)
    start_date = models.DateField()
    wip_lower_bound = models.PositiveSmallIntegerField()
    wip_upper_bound = models.PositiveSmallIntegerField()
    split_factor_lower_bound = models.FloatField()
    split_factor_upper_bound = models.FloatField()
    throughput_period_length = models.PositiveSmallIntegerField()
    throughput_lower_bound = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.forecast_text

    def generate_forecast_output(self):
        return "in 10 days we're done for " + self.forecast_text
