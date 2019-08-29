import re
from django.db.models import Q


def parse_filter(filter_str, wip_from_data):
    dict_filter = {comp[0]: comp[1]
                   for comp in map(lambda x: re.split('=|<=', x),
                                   filter(None, re.split(';', filter_str)))} if wip_from_data else {}
    print(f"DICT FILTER IS: {dict_filter}")
    return Q(**dict_filter)
