from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from forecast.helperMethods.rest import fetch_filters_and_update_form, create_form_filters
from forecast.helperMethods.forecast_models_utils import aggregate_simulations
from .models import Query, Simulation, Form


def index(request):
    query_list = Query.objects.order_by('-creation_date')

    context = {'query_list': query_list,
               'nbar': 'index'}

    return render(request, 'forecast/index.html', context)


def detail(request, query_id, run_simulation_response=None):
    # TODO: refresh shows as a GET
    query = get_object_or_404(Query, pk=query_id)

    fetch_filters_and_update_form(query.form)

    latest_simulation_list = query.simulation_set.order_by('-creation_date')

    (centile_values, weeks, weeks_frequency, weeks_frequency_sum) = \
        aggregate_simulations(latest_simulation_list.first()) \
        if latest_simulation_list.exists() \
        else ([], [], [], None)

    context = {'query': query,
               'form': query.form,
               'latest_simulation_list': latest_simulation_list,
               'weeks': weeks,
               'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
               'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
               'centile_indices': [5*i for i in range(0, 21)],
               'centile_values': centile_values,
               'nbar': 'detail',
               'run_simulation_response': run_simulation_response}

    return render(request, 'forecast/detail.html', context)


def results(request, query_id, simulation_id):
    query = get_object_or_404(Query, pk=query_id)

    simulation = get_object_or_404(Simulation, pk=simulation_id)

    centile_values, weeks, weeks_frequency, weeks_frequency_sum = aggregate_simulations(simulation)

    context = {
        'query': query,
        'weeks': weeks,
        'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
        'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
        'centile_indices': [5*i for i in range(0, 21)],
        'centile_values': centile_values,
        'nbar': 'results'
    }

    return render(request, 'forecast/results.html', context)


def run_simulation(request, query_id):

    wip_filter = request.POST['wip_filter']

    throughput_filter = request.POST['throughput_filter']

    Form.objects \
        .filter(query__pk=query_id) \
        .update(wip_lower_bound=int(request.POST['wip_lower_bound']),
                wip_upper_bound=int(request.POST['wip_upper_bound']),
                wip_filter=wip_filter,
                throughput_lower_bound=float(request.POST['throughput_lower_bound']),
                throughput_upper_bound=float(request.POST['throughput_upper_bound']),
                throughput_filter=throughput_filter,
                split_factor_lower_bound=float(request.POST['split_factor_lower_bound']),
                split_factor_upper_bound=float(request.POST['split_factor_upper_bound']),
                simulation_count=int(request.POST['simulation_count']))

    query = get_object_or_404(Query, pk=query_id)

    run_simulation_response = query.create_simulation()

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:detail', args=(query_id, run_simulation_response,)))


def create_query(request):
    # TODO: check validity before creation of _filter and other fields
    query = Query(name=request.POST['name'], description=request.POST['description'])

    query.save()

    wip_filter, throughput_filter = create_form_filters(request.POST['filter'])

    Form.objects.create(query=query,
                        name="default Form",
                        wip_filter=wip_filter,
                        throughput_filter=throughput_filter)

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:index'))
