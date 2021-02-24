import configparser
import datetime
import operator
import re
from typing import Optional, Mapping, Dict, Any

import deal
from PIL import UnidentifiedImageError

from opensource_watchman.api.github import GithubRepoAPI
from opensource_watchman.composer import AdvancedComposer
from opensource_watchman.utils.images import get_image_height_in_pixels


@deal.pure
@deal.ensure(lambda _: _.result.owner == _.owner)
@deal.ensure(lambda _: _.result.github_api_token == _.github_api_token)
def create_api(
    owner: str,
    repo_name: str,
    github_login: str,
    github_api_token: str,
) -> GithubRepoAPI:
    return GithubRepoAPI(owner, repo_name, github_login, github_api_token)


def fetch_readme_content(api: GithubRepoAPI, readme_file_name: str) -> Optional[str]:
    return api.fetch_file_contents(readme_file_name)


def fetch_ci_config_content(api: GithubRepoAPI, ci_config_file_name: str):
    return api.fetch_file_contents(ci_config_file_name)


def fetch_file_with_package_name_content(api: GithubRepoAPI, package_name_path: str):
    return api.fetch_file_contents(
        package_name_path.split(':')[0],
    )


def fetch_repo_info(api: GithubRepoAPI):
    return api.fetch_repo_info()


def fetch_last_commit_date(api: GithubRepoAPI):
    commits = api.fetch_commits()
    last_commit_date = None
    if commits:
        raw_date = commits[0]['commit']['committer']['date']
        last_commit_date = datetime.datetime.fromisoformat(raw_date[:-1])
    return last_commit_date


def fetch_open_issues(api: GithubRepoAPI):
    return api.fetch_open_issues()


def fetch_issues_comments(api: GithubRepoAPI, open_issues):
    return {
        i['number']: api.fetch_issue_comments(i['number']) for i in open_issues
    }


def fetch_open_pull_requests(api: GithubRepoAPI):
    return api.fetch_open_pull_requests()


def fetch_detailed_pull_requests(api: GithubRepoAPI, open_pull_requests):
    pull_requests = {}
    for pull_request in open_pull_requests:
        pr = api.fetch_pull_request(pull_request['number'])
        if pr:
            pull_requests[pr['number']] = pr
    return pull_requests


def fetch_pull_request_details(api: GithubRepoAPI, detailed_pull_requests: Mapping[int, Mapping]):
    pull_request_details: Dict[int, Dict[str, Any]] = {p: {} for p in detailed_pull_requests.keys()}
    for pull_request in detailed_pull_requests.values():
        pr_commits = api.fetch_commits(pull_request_number=pull_request['number'])
        last_commit_sha = pr_commits[-1]['sha'] if pr_commits else None
        pull_request_details[pull_request['number']]['last_commit_sha'] = last_commit_sha

        last_status = api.fetch_commit_status(last_commit_sha) if last_commit_sha else None
        pull_request_details[pull_request['number']]['statuses_info'] = last_status

        reviews = api.fetch_commit_reviews(last_commit_sha) if last_commit_sha else None
        last_review = max(reviews, key=operator.itemgetter('submitted_at')) if reviews else None
        pull_request_details[pull_request['number']]['last_review'] = last_review

        pr_comments = api.fetch_pull_request_comments(pull_request['number'])
        pull_request_details[pull_request['number']]['comments'] = pr_comments
    return pull_request_details


@deal.pure
@deal.post(lambda r: r is None or r.endswith('.'))
def fetch_project_description(repo_info: Mapping[str, str]) -> Optional[str]:
    raw_description = repo_info.get('description') if repo_info else None
    if raw_description and not raw_description.endswith('.'):
        raw_description = f'{raw_description}.'
    return raw_description


def fetch_ow_repo_config(api: GithubRepoAPI, config_file_name: str, config_section_name: str):
    config = {}
    config_file_content = api.fetch_file_contents(config_file_name)
    if config_file_content:
        parser = configparser.ConfigParser()
        parser.read_string(config_file_content)
        config = dict(parser[config_section_name]) if config_section_name in parser else {}
    return config


@deal.post(lambda r: all(u.startswith('http') for u in r))
def fetch_badges_urls(readme_content: str):
    if not readme_content:
        return []
    image_urls = re.findall(r'(?:!\[.*?\]\((.*?)\))', readme_content)
    max_badge_height = 60
    badges_urls = []
    for url in image_urls:
        try:
            height = get_image_height_in_pixels(url)
        except UnidentifiedImageError:  # this happens with svg, should parse it and get height
            badges_urls.append(url)
            continue
        if height and height < max_badge_height:
            badges_urls.append(url)
    return badges_urls


@deal.pure
@deal.post(lambda r: r._functions)
def create_github_pipeline(**kwargs) -> AdvancedComposer:
    return AdvancedComposer().update_parameters(**kwargs).update_without_prefix(
        'create_',
        create_api,
    ).update_without_prefix(
        'fetch_',
        fetch_readme_content,
        fetch_ci_config_content,
        fetch_file_with_package_name_content,
        fetch_repo_info,
        fetch_last_commit_date,
        fetch_open_issues,
        fetch_issues_comments,
        fetch_open_pull_requests,
        fetch_detailed_pull_requests,
        fetch_pull_request_details,
        fetch_project_description,
        fetch_ow_repo_config,
        fetch_badges_urls,
    )
