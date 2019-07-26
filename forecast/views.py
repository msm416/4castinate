import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Team, Iteration, Form, Output
from collections import Counter

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def index(request):
    latest_team_list = Team.objects.order_by('-pub_date')[:5]
    context = {'latest_team_list': latest_team_list}
    return render(request, 'forecast/index.html', context)


def detail(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    return render(request, 'forecast/detail.html', {'team': team})


def results(request, team_id, form_id):
    team = get_object_or_404(Team, pk=team_id)
    outputs = []
    for sample in Output.objects.filter(form=form_id):
        outputs.append(sample.completion_duration)
    weeks_to_frequency = sorted(Counter(outputs).items())
    weeks = [k for (k, v) in weeks_to_frequency]
    weeks_frequency = [v for (k, v) in weeks_to_frequency]
    weeks_frequency_sum = sum(weeks_frequency)

    outputs.sort()
    fifth_centile = 0
    centile_values = []
    while fifth_centile <= weeks_frequency_sum:
        centile_values.append(outputs[fifth_centile])
        fifth_centile += int(weeks_frequency_sum / 20 - 1)

    return render(request, 'forecast/results.html', {
        'team': team,
        'weeks': weeks,
        'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
        'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
        'centile_indices': [5*i for i in range(0, 21)],
        'centile_values': centile_values
    })


def estimate(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    try:
        selected_form = \
            team.form_set.get(pk=request.POST['form'])
    except (KeyError, Form.DoesNotExist):
        # Redisplay the team voting form.
        return render(request, 'forecast/detail.html', {
            'team': team,
            'error_message': "You didn't select a forecast input.",
        })
    else:
        selected_form.is_selected = True
        selected_form.save()
        selected_form.gen_output()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(
            reverse('forecast:results',
                    args=(team.id, selected_form.id)))


@require_POST
@csrf_exempt
def webhook(request):
    data = json.loads(request.body)
    # process_webhook(data)
    return 200, 'Processed.'
