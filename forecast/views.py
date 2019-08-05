import random
import json
import requests

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from ebdjango.settings import API_TOKEN, JIRA_EMAIL, JIRA_URL
from .models import Board, Form, Simulation
from collections import Counter

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def index(request):
    latest_board_list = Board.objects.order_by('-pub_date')[:5]
    context = {'latest_board_list': latest_board_list}
    return render(request, 'forecast/index.html', context)


def detail(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    return render(request, 'forecast/detail.html', {'board': board})


def results(request, board_id, form_id):
    board = get_object_or_404(Board, pk=board_id)
    form = get_object_or_404(Form, pk=form_id)
    simulations = []
    for sample in Simulation.objects.filter(form=form_id):
        simulations.append(sample.completion_duration)
    weeks_to_frequency = sorted(Counter(simulations).items())
    weeks = [k for (k, v) in weeks_to_frequency]
    weeks_frequency = [v for (k, v) in weeks_to_frequency]
    weeks_frequency_sum = sum(weeks_frequency)

    simulations.sort()
    centile_indices = []
    centile_values = []

    for i in range(0, 21):
        centile_indices.append(5 * i)
        centile_values.append(simulations[int((weeks_frequency_sum - 1) * 5 * i / 100)])

    return render(request, 'forecast/results.html', {
        'board': board,
        'form': form,
        'weeks': weeks,
        'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
        'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
        'centile_indices': [5*i for i in range(0, 21)],
        'centile_values': centile_values
    })


def estimate(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    try:
        selected_form = board.form_set.get(pk=request.POST['form'])
    except (KeyError, Form.DoesNotExist):
        # Redisplay the board voting form.
        return render(request, 'forecast/detail.html', {
            'board': board,
            'error_message': "You didn't select a forecast input.",
        })
    else:
        selected_form.gen_simulations()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(
            reverse('forecast:results',
                    args=(board.id, selected_form.id)))


def fetch_and_process_jira_sprint_issues(sprint_id):
    # TODO: REFACTOR URL (i.e. change JIRA_URL var)
    response = requests.request(
        "GET",
        f"{JIRA_URL}/sprint/{sprint_id}/issue",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    throughput = 0

    for issue in response_as_dict['issues']:
        if issue['fields']['resolution'] is None:
            # TODO: WHAT IS THIS? RUNNING SPRINT?
            continue

        if str(issue['fields']['resolution']['name']) == "Done":
            throughput += 1

    return throughput


def fetch_and_process_jira_closed_sprints(board_jira_id, board_name):

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board/{board_jira_id}/backlog",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    if 'issues' not in response_as_dict:
        return
    if not response_as_dict['issues']:
        return

    # TODO: UNDERSTAND FORMAT AND WHY 0. Possibly wrong way to search for closed sprints
    closed_sprints = response_as_dict['issues'][0]['fields']['closedSprints']

    board = Board.objects.get(description=board_name)

    # TODO: DURATION OF SPRINT
    for sprint in closed_sprints:
        if board\
                .iteration_set\
                .filter(description=sprint['name'])\
                .count() == 0:

            throughput = fetch_and_process_jira_sprint_issues(sprint['id'])
            if throughput == 0:
                continue

            board\
                .iteration_set\
                .create(description=sprint['name'],
                        source='JIRA',
                        throughput=throughput)


def fetch_and_process_jira_boards():

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    response_boards = response_as_dict['values']

    for board in response_boards:
        if Board\
                .objects\
                .filter(description=board['name'])\
                .count() == 0:
            new_board = Board(description=board['name'],
                              pub_date=timezone.now(),
                              project_name=board['location']['name'],
                              data_sources='JIRA',
                              board_type=board['type'])
            new_board.save()

        fetch_and_process_jira_closed_sprints(board['id'], board['name'])
        # TODO: MODEL IN-PROGRESS SPRINT (at every time, there is at most
        #  one in-progress sprint and if it is closed, act accordingly)


def fetch(request):
    fetch_and_process_jira_boards()
    return HttpResponseRedirect(reverse('forecast:index'))


@require_POST
@csrf_exempt
def webhook(request):
    # data = json.loads(request.body)
    board = get_object_or_404(Board, pk=1)

    if Form.objects.count() < 10:
        aux = random.randint(0, 10000)
        board.form_set.create(description=str(aux))

    return render(request, 'forecast/detail.html', {'board': board})
