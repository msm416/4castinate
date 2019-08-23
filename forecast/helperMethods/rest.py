import json
import time

import Crypto
import oauth2 as oauth
import requests
from multiprocessing import Pool
from functools import reduce

from django.utils import timezone

from ebdjango.settings import JIRA_URL, JIRA_OAUTH_TOKEN, JIRA_OAUTH_TOKEN_SECRET, JIRA_EMAIL, JIRA_API_TOKEN
from forecast.helperMethods.oauth.jira_oauth_script import SignatureMethod_RSA_SHA1, create_oauth_client
from forecast.models import Board, Iteration, Issue, LONG_TIME_AGO, Form
from datetime import datetime

JIRA_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


def make_single_get_req(url, index, client=None, fields=''):
    # You need to do Random.atfork() in the child process after every call
    # to os.fork() to avoid reusing PRNG state
    Crypto.Random.atfork()

    url += f"?startAt={index}{fields}"
    print(f"********** MAKING GET REQUEST FOR URL: {url} - index: {index} **********")
    if client:
        # OAUTH REQUEST
        resp_code, response_content = client.request(url, "GET")
    else:
        # BASIC REQUEST
        response = requests.request(
            "GET",
            url,
            headers={"Accept": "application/json"},
            auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
            verify=False)

        resp_code = response.status_code

        response_content = response.text

    return resp_code, json.loads(response_content)


# Figure out what type of authentication method should be used
def make_aggregate_get_req(url, aggregate_key, fields, max_pages_retrieved=2):
    client = create_oauth_client(oauth.Consumer('OauthKey',
                                                'dont_care'),
                                 SignatureMethod_RSA_SHA1(),
                                 oauth.Token(JIRA_OAUTH_TOKEN,
                                             JIRA_OAUTH_TOKEN_SECRET)) if True else None
                                                               # TODO: if str(JIRA_EMAIL).find('@') == -1:
    # list of issue_lists
    aggregate_values = []

    is_last = False

    index = 0

    resp_code = -1

    while not is_last:
        resp_code, response_content = make_single_get_req(url, index, client, fields)

        aggregate_values.append(response_content[aggregate_key])

        max_results = response_content['maxResults']

        total_issues = response_content['total'] if 'total' in response_content else 0

        if 'isLast' in response_content:
            # GET BOARDS
            is_last = response_content['isLast']
        else:
            # GET ISSUES
            if max_results + index >= total_issues:
                is_last = True
            else:
                                                     # total_issues
                start_positions = range(max_results, total_issues, max_results)

                # for parallelization_index in start_positions:
                #     parallelization_resp_code, parallelization_response_content = \
                #         make_single_get_req(url, parallelization_index, client, fields)
                #
                #     aggregate_values.append(parallelization_response_content[aggregate_key])

                pool = Pool()
                unprocessed_results_map = pool.starmap(make_single_get_req,
                                                       [(url, parallelization_index, client, fields)
                                                        for parallelization_index in start_positions])
                pool.close()
                pool.join()

                aggregate_values = reduce((lambda aggr_vals, resp_tuple: aggr_vals if aggr_vals.append(resp_tuple[1][aggregate_key])
                                                                               else aggr_vals),
                                          unprocessed_results_map,
                                          aggregate_values)

                is_last = True

        max_pages_retrieved -= 1
        if max_pages_retrieved == 0:
            is_last = True

        index += max_results

        resp_code = int(resp_code['status'])

    return resp_code, \
           [value
            for value_list in aggregate_values
            for value in value_list], \
           total_issues


def jira_get_issues(board_jira_id, board, start_get_all_boards_time, fetch_date):
    # Get issues for board
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-boardId-issue-get
    # Description: Returns all issues from a board, for a given board ID.
    # This only includes issues that the user has permission to view.
    # An issue belongs to the board if its status is mapped to the board's column.
    # Epic issues do not belongs to the scrum boards.
    # Note, if the user does not have permission to view the board, no issues will be returned at all.
    # Issues returned from this resource include Agile fields, like sprint, closedSprints, flagged, and epic.
    # By default, the returned issues are ordered by rank.

    resp_code, response_as_dict, total_issues = make_aggregate_get_req(f"{JIRA_URL}/board/{board_jira_id}/issue",
                                                         'issues',
                                                         "&fields=resolution,issuetype,summary,parent,closedSprints")

    board_sprints_bulk_dict = {}

    board_issues_bulk = []

    # {'Epic parent's name': 'WIP of Epic'}
    board_epic_parents_dict = {}

    board_epic_parents_forms_bulk = []

    print(f"{time.time() - start_get_all_boards_time} LOAD JSON RESPONSE FROM REST API GET ISSUES CALL")

    hidden_throughput = 0
    hidden_id = 0
    hidden_duration = 0
    # TODO: hidden_duration for kanban boards (currently is 0)
    #       Also design partial hidden iteration throughput
    #       (currently,you either take the throughput as a whole or not)

    for issue in response_as_dict:
        # print(f"{type(issue)} !@$!@$!$@@!$!@: {issue}")
        state = 'Done' if issue['fields']['resolution'] else 'Ongoing'
        issue_type = issue['fields']['issuetype']['name']
        name = issue['fields']['summary']
        source_id = issue['id']

        # TODO: get epic parent (if any) properly:
        #       it's not necessarily direct parent (and even this might be wrong)

        if 'parent' in issue['fields']:
            epic_parent = issue['fields']['parent']['fields']['summary']
            if state == 'Ongoing':
                board_epic_parents_dict[epic_parent] = board_epic_parents_dict.get(epic_parent, 0) + 1
        else:
            epic_parent = 'None'

        board_issues_bulk.append(Issue(board=board,
                                 name=name,
                                 state=state,
                                 issue_type=issue_type,
                                 epic_parent=epic_parent,
                                 source='JIRA',
                                 source_id=source_id))

        issue_fields = issue['fields']

        if state != 'Done':
            # DON"T CONSIDER ONGOING ISSUES IN THROUGHPUT
            continue

        if issue_type == "Epic":
            # DON"T CONSIDER EPIC ISSUES IN THROUGHPUT
            continue

        if 'closedSprints' not in issue_fields:
            # ADD TO HIDDEN SPRINT ALL THOSE ISSUES
            hidden_throughput += 1
            continue

        sprint = issue_fields['closedSprints'][0]
        start_date = datetime.strptime(sprint['startDate'].split('Z')[0].split('+')[0], JIRA_DATE_FORMAT)
        complete_date = datetime.strptime(sprint['completeDate'].split('Z')[0].split('+')[0], JIRA_DATE_FORMAT)
        duration = (complete_date - start_date).days
        duration = 1 if duration is 0 else duration
        sprint_id = sprint['id']

        sprint_obj = Iteration(board=board,
                               name=sprint['name'],
                               source='JIRA',
                               throughput=0,
                               duration=duration,
                               start_date=sprint['startDate'],
                               source_id=sprint_id,
                               state=sprint['state'])

        board_sprints_bulk_dict[sprint_id] = [sprint_obj,
                                        1 + (board_sprints_bulk_dict[sprint_id][1]
                                             if sprint_id in board_sprints_bulk_dict
                                             else 0)]

    for sprint, throughput in board_sprints_bulk_dict.values():
        sprint.throughput = throughput
        hidden_duration += sprint.duration

    board_sprints_bulk_dict[hidden_id] = [(Iteration(board=board,
                                                     name=f"QUASI-ITERATION - {board.name}",
                                                     source='JIRA',
                                                     throughput=hidden_throughput,
                                                     duration=hidden_duration,
                                                     source_id=hidden_id,
                                                     state='closed',
                                                     start_date=datetime.strptime(LONG_TIME_AGO, "%Y-%m-%d"))),
                                          hidden_throughput]

    for epic_parent, wip in board_epic_parents_dict.items():
        board_epic_parents_forms_bulk.append(Form(board=board,
                                                  name=f"AUTO-FORM - {epic_parent} - {board.name}",
                                                  wip_from_data=True,
                                                  wip_lower_bound=wip,
                                                  wip_upper_bound=wip,
                                                  throughput_from_data=False))

    board_iterations_bulk = [sprint for sprint, throughput in board_sprints_bulk_dict.values()]

    return resp_code, board_issues_bulk, board_iterations_bulk, board_epic_parents_forms_bulk, total_issues


def jira_get_boards():
    # GET all boards
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-get
    # Description: Returns all boards. This only includes boards that the user has permission to view.

    start_get_all_boards_time = time.time()

    # TODO: FOR SERVER: change url to https://4cast.atlassian.net/rest/agile/latest/board

    resp_code, response_as_dict, _ = make_aggregate_get_req(f"{JIRA_URL}/board", 'values', '', 0)

    print(f"{time.time() - start_get_all_boards_time} LOAD JSON RESPONSE FROM REST API GET BOARDS CALL")

    fetch_date = timezone.now()

    Board.objects.filter(data_sources='JIRA').delete()

    boards_bulk = []

    print(f"{time.time() - start_get_all_boards_time} DELETED PREVIOUS JIRA BOARDS")

    for board in response_as_dict:

        board_obj = Board(name=board['name'],
                          creation_date=fetch_date,
                          # project_name=board['location']['name'], TODO: why is no location key in jira server resp
                          data_sources='JIRA',
                          board_type=board['type'],
                          source_id=board['id'])

        boards_bulk.append(board_obj)

    Board.objects.bulk_create(boards_bulk)

    print(f"{time.time() - start_get_all_boards_time} CREATED NEW JIRA BOARDS")

    # TODO: see if can loop through boards_bulk instead (so no objects.get())
    # These lists are lists of lists.
    issues_bulk, iterations_bulk, epic_parents_forms_bulk = [], [], []
    total_total_issues = 0
    for board in response_as_dict:
        print(f"{time.time() - start_get_all_boards_time} FLUSHING EVERYTHING FOR BOARD {board['id']}")

        board_model = Board.objects.get(data_sources='JIRA', source_id=board['id'])

        board_model.issue_set.all().delete()
        board_model.iteration_set.all().delete()
        board_model.form_set.all().delete()

        print(f"{time.time() - start_get_all_boards_time} CREATING EVERYTHING FOR BOARD {board['id']}")

        resp_code, board_issues_bulk, board_iterations_bulk, board_epic_parents_forms_bulk, total_issues = \
            jira_get_issues(board['id'],
                            board_model,
                            start_get_all_boards_time,
                            fetch_date)

        issues_bulk.append(board_issues_bulk)
        iterations_bulk.append(board_iterations_bulk)
        epic_parents_forms_bulk.append(board_epic_parents_forms_bulk)
        total_total_issues += total_issues

        print(f"{time.time() - start_get_all_boards_time} CREATED EVERYTHING FOR BOARD {board['id']}")

    Issue.objects.bulk_create([issue
                               for issue_list in issues_bulk
                               for issue in issue_list])

    Iteration.objects.bulk_create([iteration
                                   for iteration_list in iterations_bulk
                                   for iteration in iteration_list])

    Form.objects.bulk_create([epic_parent_form
                              for epic_parent_form_list in epic_parents_forms_bulk
                              for epic_parent_form in epic_parent_form_list])

    print(f"{time.time() - start_get_all_boards_time} CREATED EVERYTHING FOR ALL BOARDS IN DB - WE'RE DONE")

    print(f"{total_total_issues} - TOT")
    return resp_code
