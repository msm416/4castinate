import json
import Crypto
import oauth2 as oauth
import requests
from multiprocessing import Pool
from functools import reduce
import dateutil.parser

from ebdjango.settings import JIRA_URL, JIRA_OAUTH_TOKEN, JIRA_OAUTH_TOKEN_SECRET, JIRA_EMAIL, JIRA_API_TOKEN
from forecast.helperMethods.oauth.jira_oauth_script import SignatureMethod_RSA_SHA1, create_oauth_client

client = create_oauth_client('OauthKey', 'dont_care',
                             SignatureMethod_RSA_SHA1(),
                             oauth.Token(JIRA_OAUTH_TOKEN,
                                         JIRA_OAUTH_TOKEN_SECRET)) if True else None
                                                           # TODO: if str(JIRA_EMAIL).find('@') == -1:


JQL_ORDER_BY_CLAUSE = " ORDER BY resolutiondate "


def create_form_filters(filter):
    return f"{filter} and resolution is EMPTY", f"{filter} and resolution = done"


def fetch_filters_and_update_form(form):
    fetch_wip_filter(form)
    fetch_throughput_filter(form)
    form.save()


def fetch_wip_filter(form):
    resp_code, response_content = \
        make_single_get_req(f"{JIRA_URL}/rest/api/2/search?jql={form.wip_filter}&maxResults=1&fields=None")
    if resp_code == 200:
        form.wip_lower_bound = form.wip_upper_bound = response_content['total']
        return
    form.wip_lower_bound = form.wip_upper_bound = -1


def fetch_throughput_filter(form):
    resp_code_asc, response_content_asc = \
        make_single_get_req(f"{JIRA_URL}/rest/api/2/search?jql={form.throughput_filter} "
                            f"ORDER BY resolutiondate ASC &maxResults=1&fields=resolutiondate",
                            client)

    if resp_code_asc == 200:
        total = response_content_asc['total']

        resp_code_desc, response_content_desc = \
            make_single_get_req(f"{JIRA_URL}/rest/api/2/search?jql={form.throughput_filter} "
                                f"ORDER BY resolutiondate DESC &maxResults=1&fields=resolutiondate",
                                client)

        if len(response_content_asc['issues']) != 0 and len(response_content_desc['issues']) != 0:
            first_issue_done_date = response_content_asc['issues'][0]['fields']['resolutiondate']
            last_issue_done_date = response_content_desc['issues'][0]['fields']['resolutiondate']

            if first_issue_done_date and last_issue_done_date:

                duration_in_weeks = ((dateutil.parser.parse(last_issue_done_date) -
                                     dateutil.parser.parse(first_issue_done_date)).days + 1) / 7

                form.throughput_lower_bound = form.throughput_upper_bound = total / duration_in_weeks
                return

    form.throughput_lower_bound = form.throughput_upper_bound = -1


def make_single_get_req(url, client=None):
    # You need to do Random.atfork() in the child process after every call
    # to os.fork() to avoid reusing PRNG state
    Crypto.Random.atfork()
    print(f"********** MAKING GET REQUEST FOR URL: {url} **********")
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

    return resp_code, (json.loads(response_content) if resp_code is 200 else {})
