from collections import Counter
import numpy as np


def parse_durations_for_ui(durations):
    weeks_to_frequency = sorted(Counter(durations).items())
    centile_values = list(map(lambda x: int(x), np.percentile(durations, range(0, 101, 5), interpolation='nearest')))
    weeks_frequency_sum = sum([v for (k, v) in weeks_to_frequency])
    weeks_frequency = [v / weeks_frequency_sum for (k, v) in weeks_to_frequency]
    centile_values.sort()

    weeks = [str(k) for (k, v) in weeks_to_frequency]
    point_radius_list = [(3 if k in set(centile_values) else 0) for (k, v) in weeks_to_frequency]
    point_color_list = [("rgba(0,0,0,0.5)" if k in set(centile_values) else 0) for (k, v) in weeks_to_frequency]

    return centile_values, weeks, weeks_frequency, point_radius_list, point_color_list


def remove_order_by_from_filter(filter_str):
    pos = filter_str.lower().find(" order by")
    return filter_str[:pos] if pos != -1 else filter_str


def append_resolution_to_form_filters(filter_str):
    return f"{filter_str} and resolution is EMPTY", f"{filter_str} and resolution = done"


def list_of_primitives_as_string(primitives):
    return ';'.join(map(str, primitives))


def dispatch_estimation_ui_values(estimation):
    return (list(map(float, estimation.centile_values.split(';'))),
            estimation.weeks.split(';'),
            list(map(float, estimation.weeks_frequency.split(';'))),
            list(map(float, estimation.point_radius_list.split(';'))),
            estimation.point_color_list.split(';'))
