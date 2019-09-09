from datetime import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from forecast.helperMethods.rest import update_form_and_create_simulation
from forecast.helperMethods.utils import parse_filter
from forecast.helperMethods.forecast_models_utils import aggregate_simulations
from .models import LONG_TIME_AGO, Query, Simulation


def index(request):
    query_list = Query.objects.order_by('-creation_date')
    context = {'query_list': query_list,
               'nbar': 'index',
               'LONG_TIME_AGO': LONG_TIME_AGO}
    return render(request, 'forecast/index.html', context)


def detail(request, query_id):
    query = get_object_or_404(Query, pk=query_id)

    latest_simulation_list = query.simulation_set.order_by('-creation_date')

    (centile_values, weeks, weeks_frequency, weeks_frequency_sum) = \
        aggregate_simulations(latest_simulation_list.first()) \
        if latest_simulation_list.exists() \
        else ([], [], [], None)

    context = {'query': query,
               'form': query.form_set.get(),
               'latest_simulation_list': latest_simulation_list,
               'weeks': weeks,
               'weeks_frequency': [x / weeks_frequency_sum for x in weeks_frequency],
               'weeks_frequency_sum': ("sample size " + str(weeks_frequency_sum)),
               'centile_indices': [5*i for i in range(0, 21)],
               'centile_values': centile_values,

               'LONG_TIME_AGO': LONG_TIME_AGO,
               'nbar': 'detail'}

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


def modify_form(request, query_id):
    query = get_object_or_404(Query, pk=query_id)

    start_date = datetime.strptime(request.POST['start_date'], "%Y-%m-%d")
    throughput_from_data = True \
        if request.POST['throughput_from_data'] == "Filter" \
        else False
    wip_from_data = True \
        if request.POST['wip_from_data'] == "Filter" \
        else False
    wip_from_data_filter = request.POST['wip_from_data_filter']

    try:
        parse_filter(wip_from_data_filter, wip_from_data)
    except Exception as e:
        # PARSE ERROR
        print("***********************************CREATION ERROR**********************************")
        print(str(e))
        return detail(request, -1)
    else:
        # TODO: check validity before creation of _filter and other fields
        query.form_set.all().delete()
        query.form_set.create(
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
        return HttpResponseRedirect(reverse('forecast:detail', args=(query_id,)))


def create_query(request):
    throughput_from_data = False
    wip_from_data = False
    wip_from_data_filter = "TODO://"

    # TODO: check validity before creation of _filter and other fields
    query = Query(name=request.POST['name'], description=request.POST['description'])
    query.save()
    query.form_set.create(name="default Form")

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('forecast:index'))


def create_simulation(request, query_id):
    query = get_object_or_404(Query, pk=query_id)
    update_form_and_create_simulation(query)
    return HttpResponseRedirect(reverse('forecast:detail', args=(query_id,)))
