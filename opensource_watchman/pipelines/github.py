import configparser
import datetime
import operator
import re

from PIL import UnidentifiedImageError
from super_mario import BasePipeline, input_pipe, process_pipe

from opensource_watchman.api.github import GithubRepoAPI
from opensource_watchman.utils.images import get_image_height_in_pixels


class GithubReceiveDataPipeline(BasePipeline):
    pipeline = [
        'create_api',
        'get_target_files_content',
        'get_repo_info',
        'get_last_commit_date',
        'get_open_issues',
        'get_issues_comments',
        'get_open_pull_requests',
        'get_pull_request_info',
        'fetch_pull_request_details',
        'get_project_description',
        'get_repo_config',
        'get_badges_urls',
    ]
    @process_pipe
    @staticmethod
    def create_api(owner: str, repo_name: str, github_login: str, github_api_token: str):
        return {'api': GithubRepoAPI(owner, repo_name, github_login, github_api_token)}

    @input_pipe
    @staticmethod
    def get_target_files_content(
        api: GithubRepoAPI,
        readme_file_name,
        ci_config_file_name,
        package_name_path,
    ):
        return {
            'readme_content': api.fetch_file_contents(readme_file_name),
            'ci_config_content': api.fetch_file_contents(ci_config_file_name),
            'file_with_package_name_content': api.fetch_file_contents(
                package_name_path.split(':')[0],
            ),
        }

    @input_pipe
    @staticmethod
    def get_repo_info(api: GithubRepoAPI):
        return {'repo_info': api.fetch_repo_info()}

    @input_pipe
    @staticmethod
    def get_last_commit_date(api: GithubRepoAPI):
        commits = api.fetch_commits()
        last_commit_date = None
        if commits:
            raw_date = commits[0]['commit']['committer']['date']
            last_commit_date = datetime.datetime.fromisoformat(raw_date[:-1])
        return {'last_commit_date': last_commit_date}

    @input_pipe
    @staticmethod
    def get_open_issues(api: GithubRepoAPI):
        return {'open_issues': api.fetch_open_issues()}

    @input_pipe
    @staticmethod
    def get_issues_comments(api: GithubRepoAPI, open_issues):
        return {
            'issues_comments': {
                i['number']: api.fetch_issue_comments(i['number']) for i in open_issues
            },
        }

    @input_pipe
    @staticmethod
    def get_open_pull_requests(api):
        return {'open_pull_requests': api.fetch_open_pull_requests()}

    @input_pipe
    @staticmethod
    def get_pull_request_info(api, open_pull_requests):
        pull_requests = {}
        for pull_request in open_pull_requests:
            pr = api.fetch_pull_request(pull_request['number'])
            if pr:
                pull_requests[pr['number']] = pr
        return {'detailed_pull_requests': pull_requests}

    @input_pipe
    @staticmethod
    def fetch_pull_request_details(api, detailed_pull_requests):
        pull_request_details = {p: {} for p in detailed_pull_requests.keys()}
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
        return {'pull_request_details': pull_request_details}

    @process_pipe
    @staticmethod
    def get_project_description(repo_info):
        raw_description = repo_info.get('description') if repo_info else None
        if raw_description and not raw_description.endswith('.'):
            raw_description = f'{raw_description}.'
        return {'project_description': raw_description}

    @input_pipe
    @staticmethod
    def get_repo_config(api, config_file_name, config_section_name):
        config = {}
        config_file_content = api.fetch_file_contents(config_file_name)
        if config_file_content:
            parser = configparser.ConfigParser()
            parser.read_string(config_file_content)
            config = dict(parser[config_section_name]) if config_section_name in parser else {}
        return {'ow_repo_config': config}

    @input_pipe
    @staticmethod
    def get_badges_urls(readme_content):
        if not readme_content:
            return {'badges_urls': []}
        image_urls = re.findall(r'(?:!\[.*?\]\((.*?)\))', readme_content)
        max_badge_height = 60
        badges_urls = []
        for url in image_urls:
            height = None
            try:
                height = get_image_height_in_pixels(url)
            except UnidentifiedImageError:  # this happens with svg, should parse it and get height
                badges_urls.append(url)
                continue
            if height and height < max_badge_height:
                badges_urls.append(url)
        return {'badges_urls': badges_urls}
