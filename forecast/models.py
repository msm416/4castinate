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
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    team_data_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.team_data_text