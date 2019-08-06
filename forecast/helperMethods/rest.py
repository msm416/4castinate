import json
import requests

from django.utils import timezone

from ebdjango.settings import API_TOKEN, JIRA_EMAIL, JIRA_URL
from forecast.models import Board
from datetime import datetime


def jira_get_sprint_issues(sprint_id):
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
            # TODO: INVESTIGATE - IS THIS BACKLOG ISSUE (ISSUE THAT WAS IN SPRINT BUT NOW IS IN BACKLOG?)
            continue

        if str(issue['fields']['resolution']['name']) == "Done":
            throughput += 1

    return throughput


def jira_get_closed_sprints(board_jira_id, board_name, fetch_date):
    # TODO: Getting closed_sprints in an indirect way (and maybe wrong as well). Maybe a more specific request exists?
    # GET issues for backlog
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-boardId-backlog-get
    # Description: Returns all issues from the board's backlog, for the given board ID.
    # This only includes issues that the user has permission to view.
    # The backlog contains incomplete issues that are not assigned to any future or active sprint.
    # Note, if the user does not have permission to view the board, no issues will be returned at all.
    # Issues returned from this resource include Agile fields, like sprint, closedSprints, flagged, and epic.
    # By default, the returned issues are ordered by rank.

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board/{board_jira_id}/backlog",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    if 'issues' not in response_as_dict:
        return
    if not response_as_dict['issues']:
        return

    closed_sprints = {}

    for issue in response_as_dict['issues']:
        if 'closedSprints' in issue['fields']:
            for closed_sprint in issue['fields']['closedSprints']:
                start_date = datetime.strptime(closed_sprint['startDate'].split("T")[0], "%Y-%m-%d")
                complete_date = datetime.strptime(closed_sprint['completeDate'].split("T")[0], "%Y-%m-%d")
                duration = (start_date - complete_date).days
                duration = 1 if duration is 0 else duration
                closed_sprint['duration'] = duration
                closed_sprint['start_date'] = start_date
                # closed_sprint['complete_date'] = complete_date
                closed_sprints[closed_sprint['name']] = closed_sprint

    board = Board.objects.get(description=board_name)

    for sprint in closed_sprints.values():
        if board \
                .iteration_set \
                .filter(description=sprint['name']) \
                .count() == 0:

            throughput = jira_get_sprint_issues(sprint['id'])
            if throughput == 0:
                continue

            board \
                .iteration_set \
                .create(description=sprint['name'],
                        source='JIRA',
                        throughput=throughput,
                        duration=sprint['duration'],
                        start_date=sprint['start_date'])

    board.fetch_date = fetch_date
    board.save()


def jira_get_boards():
    # GET all boards
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-get
    # Description: Returns all boards. This only includes boards that the user has permission to view.

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

    for board in response_boards:
        if Board \
                .objects \
                .filter(description=board['name']) \
                .count() == 0:
            Board(description=board['name'],
                  creation_date=fetch_date,
                  project_name=board['location']['name'],
                  data_sources='JIRA',
                  board_type=board['type']).save()

        jira_get_closed_sprints(board['id'], board['name'], fetch_date)

        new_board = Board.objects.get(description=board['name'])
        new_board.fetch_date = fetch_date
        new_board.save()
        # TODO: MODEL IN-PROGRESS SPRINT (at every time, there is at most
        #  one in-progress sprint and if it is closed, act accordingly)
