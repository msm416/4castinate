import json
import requests
import time

from django.utils import timezone

from ebdjango.settings import API_TOKEN, JIRA_EMAIL, JIRA_URL
from forecast.models import Board, Iteration, Issue
from datetime import datetime

JIRA_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def jira_get_sprint_issues_for_throughput(sprint_id):
    # TODO: Refactor this
    # GET issues for sprint
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-sprint-sprintId-issue-get
    # Description: Returns all issues in a sprint, for a given sprint ID.
    # This only includes issues that the user has permission to view.
    # By default, the returned issues are ordered by rank.

    response = requests.request(
        "GET",
        f"{JIRA_URL}/sprint/{sprint_id}/issue",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    throughput = 0

    for issue in response_as_dict['issues']:
        if issue['fields']['resolution'] is None:
            continue

        if str(issue['fields']['resolution']['name']) == "Done":
            throughput += 1

    return throughput


def jira_get_issues(board_jira_id, board_name):
    # Get issues for board
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-boardId-issue-get
    # Description: Returns all issues from a board, for a given board ID.
    # This only includes issues that the user has permission to view.
    # An issue belongs to the board if its status is mapped to the board's column.
    # Epic issues do not belongs to the scrum boards.
    # Note, if the user does not have permission to view the board, no issues will be returned at all.
    # Issues returned from this resource include Agile fields, like sprint, closedSprints, flagged, and epic.
    # By default, the returned issues are ordered by rank.

    pre_issues_fetch = time.time()

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board/{board_jira_id}/issue",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    if not response_as_dict['issues']:
        return

    issues = {}

    board = Board.objects.get(name=board_name, data_sources='JIRA')

    board.issue_set.all().delete()

    sprints_bulk_dict = {}

    issues_bulk = []

    print(f"{time.time() - pre_issues_fetch} DELETE ISSUES, FETCH AND LOAD")

    for issue in response_as_dict['issues']:
        state = 'Done' if issue['fields']['resolution'] else 'Ongoing'
        issue_type = issue['fields']['issuetype']['name']
        name = issue['fields']['summary']
        source_id = issue['id']
        # TODO: get epic parent properly: it's not necessarily direct parent
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

        sprint_id, sprint_obj = get_closed_sprint(issue)
        sprints_bulk_dict[sprint_id] = sprint_obj

    Issue.objects.bulk_create(issues_bulk, 10000)
    # Iteration.objects.bulk_create(sprints_bulk_dict.values(), 10000)

    print(f"{time.time() - pre_issues_fetch} CREATING ISSUES")
    return


def get_closed_sprint(issue):

    return 1, 2


def jira_get_sprints(board_jira_id, board_name):
    # GET all sprints
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-boardId-sprint-get
    # Description:  Returns all sprints from a board, for a given board ID.
    # This only includes sprints that the user has permission to view.

    pre_sprints_fetch = time.time()

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board/{board_jira_id}/sprint",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    if 'errorMessages' in response_as_dict:
        # Non Scrum/Simple Jira board. Nothing to be done.
        print(response_as_dict['errorMessages'])
        return

    if not response_as_dict['values']:
        return

    sprints = {}

    post_sprints_fetch = time.time()
    print(f"{post_sprints_fetch - pre_sprints_fetch} GET SPRINTS, FETCH AND LOAD")

    for sprint in response_as_dict['values']:
        if sprint['state'] != "closed":
            # TODO: Maybe change this. For now, we add some invalid values for these fields.
            #  This is not intuitive.
            sprint['duration'] = 1
            sprint['start_date'] = timezone.now()
        else:
            start_date = datetime.strptime(sprint['startDate'], JIRA_DATE_FORMAT)
            complete_date = datetime.strptime(sprint['completeDate'], JIRA_DATE_FORMAT)
            duration = (complete_date - start_date).days
            duration = 1 if duration is 0 else duration
            sprint['duration'] = duration
            sprint['start_date'] = start_date
            # closed_sprint['complete_date'] = complete_date
        sprints[sprint['name']] = sprint

    board = Board.objects.get(name=board_name, data_sources='JIRA')

    board.iteration_set.all().delete()

    sprints_bulk = []

    print(f"{time.time() - pre_sprints_fetch} GET SPRINTS, DELETE SPRINTS, FETCH AND LOAD")

    for sprint in sprints.values():

        throughput = jira_get_sprint_issues_for_throughput(sprint['id'])

        improved_throughput = 0

        # if improved_throughput != throughput:
        #     print(")F@I@$I(@$@F(O@KFSAKOFKOSAFKOKOAFKOSAKFOAKSFKOASFKOAKOFKOAFKSAFKLSAFL"
        #           "A?SFKSAFPKPASKFPKSAFKPAKPFPKSAFKASPKFPKSAFKPSAPKFPKASFKASKFASFKPASFKPKPAS"
        #           "AKPSFPKSAFKPASKPFKPASFKPASFPKASKPFAKPFKPASFKPASFKPKPSAKPFKPASFKSAFKP")

        sprints_bulk.append(Iteration(board=board,
                                      name=sprint['name'],
                                      source='JIRA',
                                      throughput=throughput,
                                      duration=sprint['duration'],
                                      start_date=sprint['start_date'],
                                      source_id=sprint['id'],
                                      state=sprint['state']))

    Iteration.objects.bulk_create(sprints_bulk, 10000)
    print(f"{time.time() - pre_sprints_fetch} CREATING SPRINTS")


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
        verify=False
    )
    response_as_dict = json.loads(response.text)

    response_boards = response_as_dict['values']

    fetch_date = timezone.now()
    Board.objects.filter(data_sources='JIRA').delete()

    boards_bulk = []

    print(f"{time.time() - start_get_all_boards_time} DELETE BOARDS, FETCH AND LOAD")

    for board in response_boards:
        # TODO: filter by board id
        #  and add id field in model (i.e. when the name changes, overwrite the existing board)

        board_obj = Board(name=board['name'],
                          creation_date=fetch_date,
                          project_name=board['location']['name'],
                          data_sources='JIRA',
                          board_type=board['type'])

        boards_bulk.append(board_obj)

    Board.objects.bulk_create(boards_bulk, 10000)

    for board in response_boards:
        jira_get_issues(board['id'], board['name'])
        jira_get_sprints(board['id'], board['name'])

        epic_names = get_epic_names(board['id'], board['name'])

        for epic_name in epic_names:
            # TODO:
            continue

    print(f"{time.time() - start_get_all_boards_time} CREATING BOARDS")
    return response.status_code


def get_epic_names(board_id, board_name):
    return {}
