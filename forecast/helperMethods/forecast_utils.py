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


def compute_latest_estimations_change_table(estimations):
    latest_estimation_change_table = []
    earlier_entry = None

    # NOTE: WE ITERATE IN REVERSE ORDER W.R.T. HOW IT IS DISPLAYED
    # (we return the reverse list)
    for estimation in estimations:
        entry = [{"week": int(value)}
                 for value in [list(map(float, estimation.centile_values.split(';')))[i]
                               for i in [5, 10, 15, 17, 20]]]

        # Arbitrary choice to pass the  creation date of the estimation
        # in the dict coresponding to the 25th percentile
        # (which happens to be the first dict - i.e. index 0 - in entry)
        entry[0]["creation_date"] = estimation.creation_date

        if earlier_entry:
            for entry_dict, earlier_entry_dict in zip(entry, earlier_entry):
                week_dif = entry_dict["week"] - earlier_entry_dict["week"] - \
                           int((estimation.creation_date - earlier_entry_creation_date).days / 7)
                if week_dif > 0:
                    entry_dict["color"] = "red"
                    entry_dict["rem"] = f"(+{week_dif})"
                elif week_dif < 0:
                    entry_dict["color"] = "green"
                    entry_dict["rem"] = f"({week_dif})"

        latest_estimation_change_table.append(entry)
        earlier_entry = entry
        earlier_entry_creation_date = estimation.creation_date

    latest_estimation_change_table.reverse()
    return latest_estimation_change_table
