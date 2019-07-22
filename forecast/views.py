from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Team, TeamData


def index(request):
    latest_team_list = Team.objects.order_by('-pub_date')[:5]
    context = {'latest_team_list': latest_team_list}
    return render(request, 'forecast/index.html', context)


def detail(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    return render(request, 'forecast/detail.html', {'team': team})


def results(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    return render(request, 'forecast/results.html', {'team': team})


def vote(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    try:
        selected_teamdata = team.teamdata_set.get(pk=request.POST['teamdata'])
    except (KeyError, TeamData.DoesNotExist):
        # Redisplay the team voting form.
        return render(request, 'forecast/detail.html', {
            'team': team,
            'error_message': "You didn't select a teamdata.",
        })
    else:
        selected_teamdata.votes += 1
        selected_teamdata.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('forecast:results', args=(team.id,)))
