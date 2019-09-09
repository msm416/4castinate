import json
import Crypto
import oauth2 as oauth
import requests
from multiprocessing import Pool
from functools import reduce

from ebdjango.settings import JIRA_URL, JIRA_OAUTH_TOKEN, JIRA_OAUTH_TOKEN_SECRET, JIRA_EMAIL, JIRA_API_TOKEN
from forecast.helperMethods.oauth.jira_oauth_script import SignatureMethod_RSA_SHA1, create_oauth_client

JIRA_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

client = create_oauth_client('OauthKey', 'dont_care',
                             SignatureMethod_RSA_SHA1(),
                             oauth.Token(JIRA_OAUTH_TOKEN,
                                         JIRA_OAUTH_TOKEN_SECRET)) if True else None
                                                           # TODO: if str(JIRA_EMAIL).find('@') == -1:


def fetch_filters_and_update_form(form):
    resp_code, response_content = \
        make_single_get_req(f"{JIRA_URL}/rest/api/2/search?jql={form.wip_filter}&fields=None")
    if resp_code == 200:
        form.wip_lower_bound = form.wip_upper_bound = response_content['total']
    else:
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! bad filter  !!!!!!!!!!!!!!!!!!!!!")
        form.wip_lower_bound = form.wip_upper_bound = 0
    form.save()


def update_form_and_create_simulation(query):
    fetch_filters_and_update_form(query.form_set.get())
    query.create_simulation()


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

    return resp_code, json.loads(response_content)


# Figure out what type of authentication method should be used
def make_aggregate_get_req(url, aggregate_key, fields, max_pages_retrieved=2):
    # list of issue_lists
    aggregate_values = []

    is_last = False

    index = 0

    resp_code = -1

    while not is_last:
        resp_code, response_content = make_single_get_req(f"{url}?startAt={index}{fields}", client)

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
                start_positions = range(max_results, 2 * max_results, max_results)

                # for parallelization_index in start_positions:
                #     parallelization_resp_code, parallelization_response_content = \
                #         make_single_get_req(url, parallelization_index, client, fields)
                #
                #     aggregate_values.append(parallelization_response_content[aggregate_key])

                pool = Pool()
                unprocessed_results_map = pool.starmap(make_single_get_req,
                                                       [(f"{url}?startAt={parallelization_index}{fields}", client)
                                                        for parallelization_index in start_positions])
                pool.close()
                pool.join()

                aggregate_values = reduce(
                    (lambda aggr_vals, resp_tuple: aggr_vals
                     if aggr_vals.append(resp_tuple[1][aggregate_key])
                     else aggr_vals),
                    unprocessed_results_map,
                    aggregate_values)

                is_last = True

        max_pages_retrieved -= 1
        if max_pages_retrieved == 0:
            is_last = True

        index += max_results

        resp_code = int(resp_code['status'])

    return resp_code, [value for value_list in aggregate_values for value in value_list], total_issues
