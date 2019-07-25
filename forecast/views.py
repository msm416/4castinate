from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Team, TeamData, ForecastInput, ForecastOutputSample
from collections import Counter

def index(request):
    latest_team_list = Team.objects.order_by('-pub_date')[:5]
    context = {'latest_team_list': latest_team_list}
    return render(request, 'forecast/index.html', context)


def detail(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    return render(request, 'forecast/detail.html', {'team': team})


def results(request, team_id, forecastinput_id):
    team = get_object_or_404(Team, pk=team_id)
    forecastoutputsamples = []
    for sample in ForecastOutputSample.objects.filter(forecastinput=forecastinput_id):
        forecastoutputsamples.append(sample.completion_duration)
    forecastoutputsamples = sorted(Counter(forecastoutputsamples).items())
    weeks = [k for (k, v) in forecastoutputsamples]
    weeks_counts = [v for (k, v) in forecastoutputsamples]

    return render(request, 'forecast/results.html', {
        'team': team,
        'forecast_weeks': weeks,
        'forecast_weeks_counts': [x / sum(weeks_counts) for x in weeks_counts],
        'debug_weeks_aux': str(sum(weeks_counts)),

        ##TODO: remove debug_weeks_aux when done with debugging this feature
    })


def estimate(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    try:
        selected_forecastinput = \
            team.forecastinput_set.get(pk=request.POST['forecastinput'])
    except (KeyError, ForecastInput.DoesNotExist):
        # Redisplay the team voting form.
        return render(request, 'forecast/detail.html', {
            'team': team,
            'error_message': "You didn't select a forecast input.",
        })
    else:
        selected_forecastinput.is_selected = True
        selected_forecastinput.save()
        selected_forecastinput.generate_forecast_output()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(
            reverse('forecast:results',
                    args=(team.id, selected_forecastinput.id)))
