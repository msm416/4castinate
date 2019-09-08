from forecast.models import Simulation

from collections import Counter


def aggregate_simulations(simulation):
    simulations = [int(x) for x in
                   simulation.durations.split(";")]

    weeks_to_frequency = sorted(Counter(simulations).items())

    weeks = [k for (k, v) in weeks_to_frequency]
    weeks_frequency = [v for (k, v) in weeks_to_frequency]

    weeks_frequency_sum = sum(weeks_frequency)

    # weeks = [k for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]
    # weeks_frequency = [v for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]

    # TODO: fiecare 20-ish element are pe oY average prob in loc de prob discreta (sa fie omogen grafu)
    weeks = [k for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]
    weeks_frequency = [v for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]

    simulations.sort()
    centile_indices = []
    centile_values = []
    for i in range(0, 21):
        centile_indices.append(5 * i)
        centile_values.append(simulations[int((weeks_frequency_sum - 1) * 5 * i / 100)])
    return centile_values, weeks, weeks_frequency, weeks_frequency_sum

