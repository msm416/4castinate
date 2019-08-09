import json
import requests

from django.utils import timezone

from ebdjango.settings import API_TOKEN, JIRA_EMAIL, JIRA_URL
from forecast.models import Board
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

    response = requests.request(
        "GET",
        f"{JIRA_URL}/board/{board_jira_id}/issue",
        headers={"Accept": "application/json"},
        auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, API_TOKEN),
        verify=False
    )

    response_as_dict = json.loads(response.text)

    if not response_as_dict['issues']:
        print("NO ISSUES!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return

    issues = {}

    board = Board.objects.get(name=board_name, data_sources='JIRA')

    board.issue_set.all().delete()

    for issue in response_as_dict['issues']:
        print("GR%LPKPRGKK$P%GKPRGPRKPGRKRPRGKPRKPGRPKRKGRPKRPGKPRG")
        state = 'Done' if issue['fields']['resolution'] else 'Ongoing'
        issue_type = issue['fields']['issuetype']['name']
        name = issue['fields']['summary']
        source_id = issue['id']
        # TODO: get epic parent properly: it's not necessarily direct parent
        epic_parent = issue['fields']['parent']['fields']['summary'] \
            if 'parent' in issue['fields'] \
            else 'None'

        board \
            .issue_set \
            .create(name=name,
                    state=state,
                    issue_type=issue_type,
                    epic_parent=epic_parent,
                    source='JIRA',
                    source_id=source_id)

    return


def jira_get_sprints(board_jira_id, board_name):
    # GET all sprints
    # https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-boardId-sprint-get
    # Description:  Returns all sprints from a board, for a given board ID.
    # This only includes sprints that the user has permission to view.

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

    for sprint in sprints.values():

        throughput = jira_get_sprint_issues_for_throughput(sprint['id'])

        board \
            .iteration_set \
            .create(name=sprint['name'],
                    source='JIRA',
                    throughput=throughput,
                    duration=sprint['duration'],
                    start_date=sprint['start_date'],
                    source_id=sprint['id'],
                    state=sprint['state'])


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
        # TODO: filter by board id
        #  and add id field in model (i.e. when the name changes, overwrite the existing board)
        if not Board \
                .objects \
                .filter(name=board['name'], data_sources='JIRA') \
                .exists():
            Board(name=board['name'],
                  creation_date=fetch_date,
                  project_name=board['location']['name'],
                  data_sources='JIRA',
                  board_type=board['type']).save()

        jira_get_sprints(board['id'], board['name'])
        jira_get_issues(board['id'], board['name'])

        the_board = Board.objects.get(name=board['name'], data_sources='JIRA')

        epic_names = get_epic_names(board['id'], board['name'])

        for epic_name in epic_names:
            # TODO:
            continue
        the_board.fetch_date = fetch_date
        the_board.save()


def get_epic_names(board_id, board_name):
    return {}
