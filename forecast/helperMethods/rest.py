import json
import requests
import time

from django.utils import timezone

from ebdjango.settings import API_TOKEN, JIRA_EMAIL, JIRA_URL
from forecast.models import Board, Iteration, Issue, LONG_TIME_AGO
from datetime import datetime

JIRA_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


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

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board/{board_jira_id}/issue",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False)

    response_as_dict = json.loads(response.text)

    if not response_as_dict['issues']:
        return

    sprints_bulk_dict = {}

    issues_bulk = []

    print(f"{time.time() - start_get_all_boards_time} LOAD JSON RESPONSE FROM REST API GET ISSUES CALL")

    hidden_throughput = 0
    hidden_id = -1
    hidden_duration = 0
    # TODO: hidden_duration for kanban boards (currently is 0)
    #       Also design partial hidden iteration throughput
    #       (currently,you either take the throughput as a whole or not)

    for issue in response_as_dict['issues']:
        state = 'Done' if issue['fields']['resolution'] else 'Ongoing'
        issue_type = issue['fields']['issuetype']['name']
        name = issue['fields']['summary']
        source_id = issue['id']
        # TODO: get epic parent (if any) properly: it's not necessarily direct parent (and even this might be wrong)
        epic_parent = issue['fields']['parent']['fields']['summary'] \
            if 'parent' in issue['fields'] \
            else 'None'

        issues_bulk.append(Issue(board=board,
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
        start_date = datetime.strptime(sprint['startDate'], JIRA_DATE_FORMAT)
        complete_date = datetime.strptime(sprint['completeDate'], JIRA_DATE_FORMAT)
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

        sprints_bulk_dict[sprint_id] = [sprint_obj,
                                        1 + (sprints_bulk_dict[sprint_id][1]
                                             if sprint_id in sprints_bulk_dict
                                             else 0)]

    for sprint, throughput in sprints_bulk_dict.values():
        sprint.throughput = throughput
        hidden_duration += sprint.duration

    sprints_bulk_dict[hidden_id] = [(Iteration(board=board,
                                               name=f"QUASI-ITERATION - {board.name}",
                                               source='JIRA',
                                               throughput=hidden_throughput,
                                               duration=hidden_duration,
                                               source_id=hidden_id,
                                               state='closed',
                                               start_date=datetime.strptime(LONG_TIME_AGO, "%Y-%m-%d"))),
                                    hidden_throughput]

    board.issue_set.all().delete()

    Issue.objects.bulk_create(issues_bulk)

    board.iteration_set.all().delete()

    Iteration.objects.bulk_create([sprint for sprint, throughput in sprints_bulk_dict.values()])


def jira_get_boards():
    # GET all boards
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-get
    # Description: Returns all boards. This only includes boards that the user has permission to view.

    start_get_all_boards_time = time.time()

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False)

    response_as_dict = json.loads(response.text)

    print(f"{time.time() - start_get_all_boards_time} LOAD JSON RESPONSE FROM REST API GET BOARDS CALL")

    response_boards = response_as_dict['values']

    fetch_date = timezone.now()

    Board.objects.filter(data_sources='JIRA').delete()

    boards_bulk = []

    print(f"{time.time() - start_get_all_boards_time} DELETED PREVIOUS JIRA BOARDS")

    for board in response_boards:

        board_obj = Board(name=board['name'],
                          creation_date=fetch_date,
                          project_name=board['location']['name'],
                          data_sources='JIRA',
                          board_type=board['type'],
                          source_id=board['id'])

        boards_bulk.append(board_obj)

    Board.objects.bulk_create(boards_bulk)

    print(f"{time.time() - start_get_all_boards_time} CREATED NEW JIRA BOARDS")

    for board in response_boards:
        print(f"{time.time() - start_get_all_boards_time} CREATING EVERYTHING FOR BOARD {board['id']}")
        jira_get_issues(board['id'],
                        Board.objects.get(data_sources='JIRA', source_id=board['id']),
                        start_get_all_boards_time,
                        fetch_date)
        print(f"{time.time() - start_get_all_boards_time} CREATED EVERYTHING FOR BOARD {board['id']}")

    print(f"{time.time() - start_get_all_boards_time} CREATED EVERYTHING - WE'RE DONE")
    return response.status_code
