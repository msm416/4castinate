import random

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from forecast.helperMethods.rest import jira_get_boards
from forecast.helperMethods.utils import aggregate_simulations
from .models import Board, Form, Iteration

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def index(request):
    latest_board_list = Board.objects.order_by('-creation_date')
    context = {'latest_board_list': latest_board_list}
    return render(request, 'forecast/index.html', context)


def detail(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    latest_form_list = board.form_set.order_by('-creation_date')
    context = {'board': board, 'latest_form_list': latest_form_list}
    return render(request, 'forecast/detail.html', context)


def results(request, board_id, form_id):
    board = get_object_or_404(Board, pk=board_id)
    form = get_object_or_404(Form, pk=form_id)
    centile_values, weeks, weeks_frequency, weeks_frequency_sum = aggregate_simulations(form_id)

    return render(request, 'forecast/results.html', {
        'board': board,
        'form': form,
        'weeks': weeks,
        'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
        'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
        'centile_indices': [5*i for i in range(0, 21)],
        'centile_values': centile_values
    })


def iterations(request):
    iteration_list = Iteration.objects.order_by('-start_date').order_by('board__description')
    context = {'iteration_list': iteration_list}
    return render(request, 'forecast/iterations.html', context)


def estimate(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    try:
        selected_form = board.form_set.get(pk=request.POST['form'])
    except (KeyError, Form.DoesNotExist):
        # Redisplay the form selection template.
        return render(request, 'forecast/detail.html', {
            'board': board,
            'error_message': "You didn't choose a form!",
        })
    else:
        selected_form.gen_simulations()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(
            reverse('forecast:results',
                    args=(board.id, selected_form.id)))


def fetch(request):
    jira_get_boards()

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:index'))


def create_form(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    throughput_from_data = True \
        if request.POST['throughput_from_data'] == "Historical Data" \
        else False
    board.form_set.create(
        description=request.POST['description'],
        throughput_from_data=throughput_from_data,
        wip_lower_bound=request.POST['wip_lower_bound'],
        wip_upper_bound=request.POST['wip_upper_bound'],
        split_factor_lower_bound=request.POST['split_factor_lower_bound'],
        split_factor_upper_bound=request.POST['split_factor_upper_bound'],
        throughput_lower_bound=request.POST['throughput_lower_bound'],
        throughput_upper_bound=request.POST['throughput_upper_bound'],
        simulation_count=request.POST['simulation_count'])

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:detail', args=(board_id,)))


@require_POST
@csrf_exempt
def webhook(request):
    # data = json.loads(request.body)
    board = get_object_or_404(Board, pk=1)

    if Form.objects.count() < 10:
        aux = random.randint(0, 10000)
        board.form_set.create(description=str(aux))

    return render(request, 'forecast/detail.html', {'board': board})
