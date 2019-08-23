from forecast.models import Simulation, Form
from collections import Counter


def aggregate_simulations(form_id):
    form = Form.objects.get(pk=form_id)

    if not form.simulation_set.exists():
        print("AAAAAAAAAAAAAA")
        form.gen_simulations()

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
