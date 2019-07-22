from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render

from .models import Team


def index(request):
    latest_team_list = Team.objects.order_by('-pub_date')[:5]
    context = {'latest_team_list': latest_team_list}
    return render(request, 'forecast/index.html', context)


def detail(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    return render(request, 'forecast/detail.html', {'team': team})


def results(request, team_id):
    response = "You're looking at the results of team %s."
    return HttpResponse(response % team_id)


def vote(request, team_id):
    return HttpResponse("You're forecasting on team %s." % team_id)