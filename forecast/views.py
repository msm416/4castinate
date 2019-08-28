import json
import random
from datetime import datetime

from django.utils import timezone

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from forecast.helperMethods.rest import jira_get_boards
from forecast.helperMethods.utils import aggregate_simulations, parse_filter
from .models import Board, Form, Iteration, LONG_TIME_AGO, Issue, MsgLogWebhook

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def index(request):
    latest_board_list = Board.objects\
                             .filter(creation_date__lte=timezone.now())\
                             .order_by('-creation_date')
    msglog_webhook_list = MsgLogWebhook.objects.all()
    context = {'latest_board_list': latest_board_list,
               'nbar': 'index',
               'msglog_webhook_list': msglog_webhook_list}
    return render(request, 'forecast/index.html', context)


def detail(request, board_id, form_id=None):
    board = get_object_or_404(Board, pk=board_id)

    prev_selected_form = board.form_set.filter(is_selected=True).first()

    if prev_selected_form:
        prev_selected_form.is_selected = False
        prev_selected_form.save()

    selected_form = Form.objects.get(id=form_id) \
        if form_id else \
        (prev_selected_form if prev_selected_form else board.form_set.first())

    if selected_form:
        selected_form.is_selected = True
        selected_form.save()
        (centile_values, weeks, weeks_frequency, weeks_frequency_sum) = aggregate_simulations(selected_form.id)
    else:
        (centile_values, weeks, weeks_frequency, weeks_frequency_sum) = ([], [], [], None)

    latest_form_list = board.form_set.order_by('-creation_date')

    context = {'board': board,
               'latest_form_list': latest_form_list,
               'form': selected_form,
               'weeks': weeks,
               'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
               'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
               'centile_indices': [5*i for i in range(0, 21)],
               'centile_values': centile_values,

               'LONG_TIME_AGO': LONG_TIME_AGO,
               'nbar': 'detail',
               'form_fields': [field.name for field in Iteration._meta.get_fields()]}

    return render(request, 'forecast/detail.html', context)


def results(request, board_id, form_id):
    board = get_object_or_404(Board, pk=board_id)
    form = get_object_or_404(Form, pk=form_id)
    centile_values, weeks, weeks_frequency, weeks_frequency_sum = aggregate_simulations(form_id)
    context = {
        'board': board,
        'form': form,
        'weeks': weeks,
        'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
        'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
        'centile_indices': [5*i for i in range(0, 21)],
        'centile_values': centile_values,
        'nbar': 'results'
    }

    return render(request, 'forecast/results.html', context)


def iterations(request):
    iteration_list = Iteration.objects.order_by('board__name', '-start_date')
    context = {'iteration_list': iteration_list, 'nbar': 'iterations'}
    return render(request, 'forecast/iterations.html', context)


def issues(request):
    issue_list = Issue.objects.order_by('board__name', '-state', 'epic_parent')
    context = {'issue_list': issue_list, 'nbar': 'issues'}
    return render(request, 'forecast/issues.html', context)


def estimate(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    latest_form_list = board.form_set.order_by('-creation_date')
    context = {'board': board, 'latest_form_list': latest_form_list, 'LONG_TIME_AGO': LONG_TIME_AGO}
    try:
        selected_form = board.form_set.get(pk=request.POST['form'])
    except (KeyError, Form.DoesNotExist):
        # Redisplay the form selection template.
        context['error_message'] = "You didn't choose an existing form!"
        context['nbar'] = 'detail'
        return render(request, 'forecast/detail.html', context)
    else:
        # TODO: make all form checks (on server or client side)
        if selected_form.throughput_lower_bound <= 0 or \
                (selected_form.throughput_from_data and selected_form.get_throughput_rate_avg() == 0):
            context['error_message'] = "Selected form has invalid throughput!"
            context['nbar'] = 'detail'
            return render(request, 'forecast/detail.html', context)
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
    start_date = datetime.strptime(request.POST['start_date'], "%Y-%m-%d")
    throughput_from_data = True \
        if request.POST['throughput_from_data'] == "Historical Data" \
        else False
    wip_from_data = True \
        if request.POST['wip_from_data'] == "Historical Data" \
        else False
    wip_from_data_filter = request.POST['wip_from_data_filter']

    # TODO: check validity before creation of _filter and other fields
    board.form_set.create(
        wip_lower_bound=int(request.POST['wip_lower_bound']),
        wip_upper_bound=int(request.POST['wip_upper_bound']),
        wip_from_data=wip_from_data,
        wip_from_data_filter=wip_from_data_filter,
        throughput_lower_bound=float(request.POST['throughput_lower_bound']),
        throughput_upper_bound=float(request.POST['throughput_upper_bound']),
        throughput_from_data=throughput_from_data,
        start_date=start_date,
        split_factor_lower_bound=float(request.POST['split_factor_lower_bound']),
        split_factor_upper_bound=float(request.POST['split_factor_upper_bound']),
        name=request.POST['name'],
        simulation_count=int(request.POST['simulation_count']))

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:detail', args=(board_id,)))


@require_POST
@csrf_exempt
def webhook(request):
    data = json.loads(request.body)

    if MsgLogWebhook.objects.exists():
        msg_log_webhook = MsgLogWebhook.objects.get(msglog_id=1)
        msg_log_webhook.text = f"{msg_log_webhook.text};{str(data)}"
        msg_log_webhook.cnt += 1
        msg_log_webhook.save()
    else:
        MsgLogWebhook.objects.create(cnt=1, text=str(data))
    return HttpResponseRedirect(reverse('forecast:index'))
