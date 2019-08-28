from forecast.models import Form, Simulation
from collections import Counter
import re


def aggregate_simulations(form_id):
    form = Form.objects.get(pk=form_id)
    simulations = [int(x) for x in
                   Simulation.objects.get(form=form_id).durations.split(";")]

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
    return centile_values, weeks, weeks_frequency, weeks_frequency_sum


def parse_filter(filter_str):
    return str({field_name: field_val
                for comp in re.split(';', filter_str)
                for field_name, field_val in re.split('=|<=', comp)})
