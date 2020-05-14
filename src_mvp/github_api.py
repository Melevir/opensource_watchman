import configparser
import datetime
import operator
import os
from typing import List, Optional, Any, Mapping

from requests import get
from requests.auth import HTTPBasicAuth


def get_repos_list(owner: str) -> List[str]:
    raw_response = get(
        f'https://api.github.com/users/{owner}/repos',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    ).json()
    raw_response.sort(key=operator.itemgetter('updated_at'))
    return [r['name'] for r in reversed(raw_response)]


def get_repo_info(owner: str, repo_name: str) -> Optional[Mapping[str, Any]]:
    raw_response = get(
        f'https://api.github.com/repos/{owner}/{repo_name}',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    return raw_response.json() if raw_response else None


def get_last_commit_date(owner: str, repo_name: str) -> Optional[datetime.datetime]:
    raw_response = get(
        f'https://api.github.com/repos/{owner}/{repo_name}/commits',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    last_commit_date = None
    if raw_response:
        raw_date = raw_response.json()[0]['commit']['committer']['date']
        last_commit_date = datetime.datetime.fromisoformat(raw_date[:-1])
    return last_commit_date


def get_file_contents(owner: str, repo_name: str, file_path: str) -> Optional[str]:
    file_url = f'https://raw.githubusercontent.com/{owner}/{repo_name}/master/{file_path}'
    response = get(file_url)
    return response.text if response else None


def get_open_issues(owner: str, repo_name: str) -> List[Mapping[str, Any]]:
    raw_response = get(
        f'https://api.github.com/repos/{owner}/{repo_name}/issues',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    return raw_response.json() if raw_response else []


def get_issue_comments(owner: str, repo_name: str, issue_number: int) -> List[Mapping[str, Any]]:
    raw_response = get(
        f'https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}/comments',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    return raw_response.json() if raw_response else []


def get_open_pull_requests(owner: str, repo_name: str) -> List[Mapping[str, Any]]:
    raw_response = get(
        f'https://api.github.com/repos/{owner}/{repo_name}/pulls',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    return raw_response.json() if raw_response else []


def get_pull_request_info(owner: str, repo_name: str, pr_number: int) -> Optional[Mapping[str, Any]]:
    raw_response = get(
        f'https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    return raw_response.json() if raw_response else None


def is_pull_request_ok_to_merge(pull_request: Mapping[str, Any]) -> bool:
    raw_commits_response = get(
        f'https://api.github.com/repos/{pull_request["base"]["repo"]["full_name"]}/pulls/{pull_request["number"]}/commits',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    if not raw_commits_response:
        print(1)
        return False
    last_commit_sha = raw_commits_response.json()[-1]['sha']

    raw_statuses_response = get(
        f'https://api.github.com/repos/{pull_request["base"]["repo"]["full_name"]}/commits/{last_commit_sha}/statuses',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    if not raw_statuses_response:
        return False
    statuses_info = raw_statuses_response.json()
    if statuses_info and statuses_info[0]['state'] != 'success':
        return False

    raw_reviews_response = get(
        f'https://api.github.com/repos/{pull_request["base"]["repo"]["full_name"]}//commits/{last_commit_sha}/reviews',
        auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
    )
    if raw_reviews_response:
        reviews_info = raw_reviews_response.json()
        last_review = max(reviews_info, key=operator.itemgetter('submitted_at')) if reviews_info else None
        if last_review and last_review['state'] == 'CHANGES_REQUESTED':
            print(3)
            return False
    return True


def get_pull_request_updated_at(pull_request: Mapping[str, Any]) -> datetime.datetime:
    updated_at = pull_request['updated_at']
    # print(pull_request)
    if pull_request['comments']:
        raw_comments_response = get(
            f'https://api.github.com/repos/{pull_request["base"]["repo"]["full_name"]}/pulls/{pull_request["number"]}/comments',
            auth=HTTPBasicAuth(os.environ.get('GITHUB_USERNAME'), os.environ.get('GITHUB_API_TOKEN')),
        )
        if raw_comments_response:
            comments = raw_comments_response.json()
            last_comment = max(comments, key=operator.itemgetter('updated_at')) if comments else None
            if last_comment and last_comment['update_at'] > updated_at:
                updated_at = last_comment['update_at']
    return datetime.datetime.fromisoformat(updated_at[:-1])


def get_project_description(owner: str, repo_name: str) -> Optional[str]:
    repo_info = get_repo_info(owner, repo_name)
    raw_description = repo_info.get('description') if repo_info else None
    if raw_description and not raw_description.endswith('.'):
        raw_description = f'{raw_description}.'
    return raw_description


def get_repo_config(owner, repo_name, config_file_name, config_section_name) -> Mapping[str, Any]:
    config_file_content = get_file_contents(owner, repo_name, config_file_name)
    if config_file_content is None:
        return {}
    parser = configparser.ConfigParser()
    parser.read_string(config_file_content)
    return dict(parser[config_section_name]) if config_section_name in parser else {}
