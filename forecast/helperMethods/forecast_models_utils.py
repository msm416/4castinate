from collections import Counter
import numpy as np


def reduce_durations(durations):
    weeks_to_frequency = sorted(Counter(durations).items())
    centile_values = list(map(lambda x: int(x), np.percentile(durations, range(0, 101, 5), interpolation='nearest')))
    weeks = [(str(k) if k in set(centile_values) else str(k)) for (k, v) in weeks_to_frequency]
    print(weeks)
    weeks_frequency = [v for (k, v) in weeks_to_frequency]

    weeks_frequency_sum = sum(weeks_frequency)
    centile_values.sort()
    print(centile_values)
    print(weeks_frequency)
    # print(weeks_frequency_sum)

    # weeks = [k for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]
    # weeks_frequency = [v for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]

    # weeks = [k for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]
    # weeks_frequency = [v for (k, v) in weeks_to_frequency][0::int(len(weeks_to_frequency)/20)]
    # print(centile_values)
    return centile_values, weeks, weeks_frequency, weeks_frequency_sum

