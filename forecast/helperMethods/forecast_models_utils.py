from collections import Counter
import numpy as np


def reduce_durations(durations):
    weeks_to_frequency = sorted(Counter(durations).items())
    centile_values = list(map(lambda x: int(x), np.percentile(durations, range(0, 101, 5), interpolation='nearest')))
    weeks_frequency = [v for (k, v) in weeks_to_frequency]

    weeks_frequency_sum = sum(weeks_frequency)
    centile_values.sort()

    weeks = [(str(k) if k in set(centile_values) else str(k)) for (k, v) in weeks_to_frequency]
    point_radius_list = [(3 if k in set(centile_values) else 0) for (k, v) in weeks_to_frequency]
    point_color_list = [("rgba(0,0,0,0.5)" if k in set(centile_values) else 0) for (k, v) in weeks_to_frequency]

    return centile_values, weeks, weeks_frequency, weeks_frequency_sum, point_radius_list, point_color_list


def remove_order_by_from_filter(filter_str):
    return filter_str[:filter_str.lower().find(" order by")]


def append_resolution_to_form_filters(filter_str):
    return f"{filter_str} and resolution is EMPTY", f"{filter_str} and resolution = done"
