import json
import Crypto
import oauth2 as oauth
import requests
import dateutil.parser

from ebdjango.settings import JIRA_URL, JIRA_OAUTH_TOKEN, JIRA_OAUTH_TOKEN_SECRET, JIRA_EMAIL, JIRA_API_TOKEN
from forecast.helperMethods.oauth.jira_oauth_script import SignatureMethod_RSA_SHA1, create_oauth_client

client = create_oauth_client('OauthKey', 'dont_care',
                             SignatureMethod_RSA_SHA1(),
                             oauth.Token(JIRA_OAUTH_TOKEN,
                                         JIRA_OAUTH_TOKEN_SECRET)) if str(JIRA_EMAIL).find('@') == -1 else None


def fetch_filters_and_update_form(form):
    initial_wip = fetch_wip_filter(form)
    initial_throughput = fetch_throughput_filter(form)
    form.save()
    return initial_wip, initial_throughput


def fetch_wip_filter(form):
    # Sets form's wip_l_b / wip_u_b to positive values (>=0) or to -1
    if form.wip_filter:
        resp_code, response_content = \
            make_single_get_req(f"{JIRA_URL}/rest/api/2/search?jql={form.wip_filter}&maxResults=1&fields=None",
                                client)

        if resp_code == 200:
            initial_wip = response_content['total']
            form.wip_lower_bound = int(response_content['total'] * (1.00 - form.split_rate_wip))
            form.wip_upper_bound = int(response_content['total'] * (1.00 + form.split_rate_wip))
            return int(initial_wip)

    # End up here if we didn't return above
    form.wip_lower_bound = form.wip_upper_bound = -1
    return -1


def fetch_throughput_filter(form):
    # Sets form's wip_l_b / wip_u_b to STRICTLY positive values (>0) or to -1
    if form.throughput_filter:
        resp_code_asc, response_content_asc = \
            make_single_get_req(f"{JIRA_URL}/rest/api/2/search?jql={form.throughput_filter}"
                                f" ORDER BY resolutiondate ASC &maxResults=1&fields=resolutiondate,updated,created",
                                client)
        if resp_code_asc == 200:
            total = response_content_asc['total']

            resp_code_desc, response_content_desc = \
                make_single_get_req(f"{JIRA_URL}/rest/api/2/search?jql={form.throughput_filter} "
                                    f" ORDER BY resolutiondate DESC &maxResults=1&fields=resolutiondate,updated,created",
                                    client)
            if len(response_content_asc['issues']) != 0 and len(response_content_desc['issues']) != 0:
                first_issue_fields = response_content_asc['issues'][0]['fields']
                last_issue_fields = response_content_desc['issues'][0]['fields']

                first_issue_done_date = first_issue_fields['resolutiondate'] if first_issue_fields['resolutiondate'] \
                    else (first_issue_fields['updated'] if first_issue_fields['updated']
                          else first_issue_fields['created'])

                last_issue_done_date = last_issue_fields['resolutiondate'] if last_issue_fields['resolutiondate'] \
                    else (last_issue_fields['updated'] if last_issue_fields['updated']
                          else last_issue_fields['created'])

                if first_issue_done_date and last_issue_done_date:
                    duration_in_weeks = ((dateutil.parser.parse(last_issue_done_date) -
                                          dateutil.parser.parse(first_issue_done_date)).days + 1) / 7

                    if duration_in_weeks != 0:
                        initial_throughput = total / duration_in_weeks
                        form.throughput_lower_bound = int(initial_throughput * (1.00 - form.split_rate_throughput))
                        form.throughput_upper_bound = int(initial_throughput * (1.00 + form.split_rate_throughput))

                        if form.throughput_lower_bound > 0:
                            return int(initial_throughput)

    # End up here if we didn't return above
    form.throughput_lower_bound = form.throughput_upper_bound = -1
    return -1


def make_single_get_req(url, oauth_client=None):
    # You need to do Random.atfork() in the child process after every call
    # to os.fork() to avoid reusing PRNG state
    Crypto.Random.atfork()

    if oauth_client:
        # OAUTH REQUEST
        req_type = "OAUTH"
        resp_code, response_content = oauth_client.request(url, "GET")

        resp_code = int(resp_code['status'])
    else:
        # BASIC HTTP REQUEST
        req_type = "BASIC HTTP REQUEST"
        response = requests.request(
            "GET",
            url,
            headers={"Accept": "application/json"},
            auth=requests.auth.HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
            verify=False)

        resp_code = response.status_code

        response_content = response.text

    print(f"********** {req_type} RESP CODE: {resp_code}: GET REQUEST FOR URL: {url} **********\n")
    return resp_code, (json.loads(response_content) if resp_code == 200 else {})
