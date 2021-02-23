import datetime
from typing import List, Tuple, Union

import pytest
import responses

from opensource_watchman.api.codeclimate_api import CodeClimateAPI
from opensource_watchman.api.github import GithubRepoAPI
from opensource_watchman.common_types import (
    RepoResult, OpensourceWatchmanConfig, GithubPipelineData,
)


class AdvancedRequestsMock(responses.RequestsMock):
    def mock_calls(self, mocks: List[Union[Tuple, str]]) -> None:
        default_method = responses.GET
        default_result = []
        for mock_info in mocks:
            url = None
            method = default_method
            result = default_result
            if isinstance(mock_info, str):
                url = mock_info
            elif len(mock_info) == 2:
                url, result = mock_info
            elif len(mock_info) == 3:
                method, url, result = mock_info
            if url:
                if isinstance(result, str):
                    kwargs = {'body': result}
                else:
                    kwargs = {'json': result}
                self.add(method, url, **kwargs)


@pytest.fixture
def ok_repo_result(owner, repo_name):
    return RepoResult(
        owner=owner,
        package_name='test',
        description='test description',
        badges_urls=[],
        repo_name=repo_name,
        errors={},
    )


@pytest.fixture
def mocked_responses():
    with AdvancedRequestsMock() as rsps:
        yield rsps


@pytest.fixture
def owner():
    return 'owner'


@pytest.fixture
def repo_name():
    return 'test_repo'


@pytest.fixture
def api_token():
    return '123-secret-api-token'


@pytest.fixture
def config_file_name():
    return 'setup.cfg'


@pytest.fixture
def github_login(owner):
    return owner


@pytest.fixture
def github_token(api_token):
    return api_token


@pytest.fixture
def config_section_name():
    return 'ow'


@pytest.fixture
def code_climate_api(mocked_responses, owner, repo_name, api_token):
    mocked_responses.add(
        responses.GET,
        f'https://api.codeclimate.com/v1/repos?github_slug={owner}/{repo_name}',
        json={'data': [{'id': 123}]},
    )
    return CodeClimateAPI.create(owner, repo_name, api_token)


@pytest.fixture
def ow_config():
    return OpensourceWatchmanConfig(
        config_file_name='setup.cfg',
        config_section_name='opensource_watchman',
        readme_file_name='README.md',
        ci_config_file_name='.travis.yml',
        package_name_path='setup.py:package_name',
        github_login='test',
        github_api_token='test',
        travis_api_login='test',
        required_readme_sections=[],
        required_commands_to_run_in_build=[],
        required_python_versions=['3.7', '3.8'],
        max_age_of_last_commit_in_months=6,
        code_climate_api_token='test',
        min_test_coverage_percents=80,
        min_number_of_actual_issues=3,
        max_issue_update_age_months=6,
        max_ok_pr_age_days=7,
    )


@pytest.fixture
def pipeline_result():
    return {
        'package_name': 'test',
        'project_description': 'test',
        'badges_urls': [],
    }


@pytest.fixture
def github_api():
    return GithubRepoAPI(
        owner='test',
        repo_name='test',
        github_login='test',
        github_api_token='123',
    )


@pytest.fixture
def detailed_pull_requests():
    return {1: {'number': 1}}


@pytest.fixture
def repos_stat_without_errors():
    return RepoResult(
        owner='test',
        package_name='test',
        description='test',
        badges_urls=[],
        repo_name='test',
        errors={},
    )


@pytest.fixture
def repos_stat_with_errors(repos_stat_without_errors):
    return RepoResult(
        owner=repos_stat_without_errors.owner,
        package_name=repos_stat_without_errors.package_name,
        description=repos_stat_without_errors.description,
        badges_urls=repos_stat_without_errors.badges_urls,
        repo_name=repos_stat_without_errors.repo_name,
        errors={'D02': ['error']},
    )


@pytest.fixture
def github_pipeline_result():
    return GithubPipelineData(
        ow_repo_config={'main_languages': 'python'},
        readme_file_name='README.md',
        readme_content='readme',
        ci_config_file_name='.travis.ci',
        ci_config_content='test:\n\t- ls',
        file_with_package_name_content='__name__ = "test"',
        last_commit_date=datetime.datetime(2021, 1, 15, 2),
        open_issues=[],
        issues_comments={},
        open_pull_requests=[],
        pull_request_details={},
        detailed_pull_requests={},
    )
