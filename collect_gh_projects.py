

import logging
import csv
import time
import requests
import pandas as pd

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

GITHUB_TOKEN = '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'
GITHUB_AUTH_HEADER = {
    'authorization': "token {0}".format(GITHUB_TOKEN),  # Add Github token
}


def search_github(N):
    '''Search github repos'''
    session = requests.Session()

    url = "https://api.github.com/search/repositories?"
    # querystring = {
    #    "q": f"language:python stars:{min}..{max}", "sort": "stars", "per_page": 100}
    querystring = {"q": f"created:2023 language:Java stars:<{N}",
                   "sort": "stars forks", "per_page": 100, "o": "desc"}

    first_page = session.get(url, params=querystring,)  # )
    yield first_page

    next_page = first_page
    while get_next_page(next_page) is not None:
        try:
            next_page_url = next_page.links['next']['url']
            next_page = session.get(
                next_page_url, params=querystring, headers=GITHUB_AUTH_HEADER)
            yield next_page

        except KeyError:
            logging.info("No more Github pages")
            break


def get_next_page(page) -> None:
    '''Returns the next page of gh'''
    return page if page.headers.get('link') != None else None


def main(n, iterations, headers):
    '''
    Iterate through pages, parse the results to a dataframe, and stop at 5000 repos.
    '''

    with open("projects_java_nexgen_validation.csv", 'w') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(headers)

        for i in range(iterations):
            logging.info("Iteration...... %s", i)

            if i != 0:
                logging.info("Sleeping zZzZzZzZzZZZzZzZzZ...")
                time.sleep(30)

            for page in search_github(n):
                try:
                    response_dict = page.json()
                    #logging.info("Total repos:", response_dict['total_count'])

                    # find total number of repositories
                    repos_dicts = response_dict['items']
                    #logging.info("Repos found:", len(repos_dicts))

                    # examine the first repository
                    for repos_dict in repos_dicts:  # loop through all the dictionaries in repos_dicts.

                        writer.writerow([repos_dict['owner']['login'], repos_dict['name'], repos_dict['html_url'], repos_dict['stargazers_count'],
                                        repos_dict['size'], repos_dict['watchers_count'], repos_dict[
                            'language'], repos_dict['has_issues'],
                            repos_dict['forks_count'], repos_dict['open_issues_count'], 'github'])

                except Exception as ex:
                    logging.info(
                        f"Error!!! parsing gh pages. exception: {str(ex)}")
                    file.close()

            df = pd.read_csv("projects_java_nexgen_validation.csv")
            n = df['stars'].min()

    df.to_csv('projects_java_nexgen_validation.csv')
    df.loc[:, ['repo_name', 'url_repo', 'source']].to_csv(
        'projects_py.csv', index=False, index_label=['name', 'repo', 'source'])


if __name__ == '__main__':
    cols = ['owner', 'repo_name', 'url_repo', 'stars',
            'size', 'watchers', 'language', 'has_issues', 'forks', 'open_issues', 'source']
    main(n=9999999, iterations=1, headers=cols)
