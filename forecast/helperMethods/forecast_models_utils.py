from collections import Counter


def reduce_durations(durations):
    weeks_to_frequency = sorted(Counter(durations).items())

    weeks = [k for (k, v) in weeks_to_frequency]
    weeks_frequency = [v for (k, v) in weeks_to_frequency]

    weeks_frequency_sum = sum(weeks_frequency)

    # weeks = [k for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]
    # weeks_frequency = [v for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]

    # weeks = [k for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]
    # weeks_frequency = [v for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]

    durations.sort()
    centile_indices = []
    centile_values = []
    for i in range(0, 21):
        centile_indices.append(5 * i)
        centile_values.append(durations[int((weeks_frequency_sum - 1) * 5 * i / 100)])
    return centile_values, weeks, weeks_frequency, weeks_frequency_sum

