from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from forecast.helperMethods.rest import fetch_filters_and_update_form
from forecast.helperMethods.forecast_utils import remove_order_by_from_filter, \
    append_resolution_to_form_filters, dispatch_estimation_ui_values
from .models import Query, Estimation, Form


def index(request):
    query_list = Query.objects.order_by('-creation_date')

    context = {
        'nbar': 'index',
        'query_list': query_list}

    return render(request, 'forecast/index.html', context)


def detail(request, query_id, run_estimation_response=None):
    query = get_object_or_404(Query, pk=query_id)

    initial_wip, initial_throughput = fetch_filters_and_update_form(query.form)

    latest_estimation_list = query.estimation_set.order_by('-creation_date')

    estimation = latest_estimation_list.first()

    weeks_frequency_sum = \
        estimation.simulation_count \
        if latest_estimation_list.exists() \
        else None

    (centile_values, weeks, weeks_frequency,
      point_radius_list, point_color_list) = \
        dispatch_estimation_ui_values(estimation) \
        if latest_estimation_list.exists() \
        else ([], [], [], [], [])

    context = {
        'nbar': 'detail',
        'query': query,
        'form': query.form,
        'run_estimation_response': run_estimation_response,
        'initial_wip': initial_wip,
        'initial_throughput': initial_throughput,
        'latest_estimation_list': latest_estimation_list,
        'centile_indices': [5*i for i in range(0, 21)],
        'centile_values': centile_values,
        'weeks': weeks,
        'weeks_frequency': weeks_frequency,
        'weeks_frequency_sum': ("SAMPLE SIZE: " + str(weeks_frequency_sum)),
        'point_radius_list': point_radius_list,
        'point_color_list': point_color_list}

    return render(request, 'forecast/detail.html', context)


def results(request, query_id, estimation_id):
    query = get_object_or_404(Query, pk=query_id)

    estimation = get_object_or_404(Estimation, pk=estimation_id)

    (centile_values, weeks, weeks_frequency, point_radius_list, point_color_list) = \
        dispatch_estimation_ui_values(estimation)

    context = {
        'nbar': 'results',
        'centile_indices': [5*i for i in range(0, 21)],
        'centile_values': centile_values,
        'query': query,
        'weeks': weeks,
        'weeks_frequency': weeks_frequency,
        'weeks_frequency_sum': ("SAMPLE SIZE: " + str(estimation.simulation_count)),
        'point_radius_list': point_radius_list,
        'point_color_list': point_color_list}

    return render(request, 'forecast/results.html', context)


def run_estimation(request, query_id):

    Form.objects \
        .filter(query__pk=query_id) \
        .update(wip_lower_bound=int(request.POST['wip_lower_bound']),
                wip_upper_bound=int(request.POST['wip_upper_bound']),
                wip_filter=remove_order_by_from_filter(request.POST['wip_filter']),
                throughput_lower_bound=float(request.POST['throughput_lower_bound']),
                throughput_upper_bound=float(request.POST['throughput_upper_bound']),
                throughput_filter=remove_order_by_from_filter(request.POST['throughput_filter']),
                split_rate_wip=float(request.POST['split_rate_wip']),
                split_rate_throughput=float(request.POST['split_rate_throughput']))

    query = get_object_or_404(Query, pk=query_id)

    run_estimation_response = query.run_estimation()

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:detail', args=(query_id, run_estimation_response,)))


def create_query(request):
    query = Query(name=request.POST['name'], description=request.POST['description'])

    query.save()

    wip_filter, throughput_filter = append_resolution_to_form_filters(
        remove_order_by_from_filter(request.POST['filter']))

    Form.objects.create(query=query,
                        wip_filter=wip_filter,
                        throughput_filter=throughput_filter)

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:index'))


def delete_estimation(request, query_id, estimation_id):
    estimation = get_object_or_404(Estimation, pk=estimation_id)
    estimation.delete()

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:detail', args=(query_id,)))


def delete_query(request, query_id):
    query = get_object_or_404(Query, pk=query_id)
    query.delete()

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:index'))
