import deal
import responses

from opensource_watchman.api.codeclimate_api import CodeClimateAPI
from opensource_watchman.api.pypistats import get_pypi_downloads_stat
from opensource_watchman.api.travis import TravisRepoAPI
from opensource_watchman.pipelines.extended_repo_info import fetch_downloads_stat


test_travis_extract_commands_from_raw_log = deal.cases(TravisRepoAPI._extract_commands_from_raw_log)


def test_get_pypi_stats(mocked_responses):
    test_project_name = 'test'
    mocked_responses.add(
        responses.GET,
        f'https://pypistats.org/api/packages/{test_project_name}/recent',
        json={'data': {'last_week': 1}},
    )

    assert get_pypi_downloads_stat(test_project_name)['last_week'] == 1


def test_fetch_downloads_stat(ok_repo_result, mocked_responses):
    mocked_responses.add(
        responses.GET,
        'https://pypistats.org/api/packages/test/recent',
        json={'data': {'last_week': 1}},
    )
    assert fetch_downloads_stat([ok_repo_result]) == {'test_repo': 1}


def test_codeclimate_get_repo_id(mocked_responses, owner, repo_name, api_token):
    mocked_responses.add(
        responses.GET,
        f'https://api.codeclimate.com/v1/repos?github_slug={owner}/{repo_name}',
        json={'data': [{'id': 123}]},
    )
    assert CodeClimateAPI(owner, repo_name, api_token, None).get_repo_id() == 123


def test_codeclomate_test_coverage(mocked_responses, code_climate_api):
    mocked_responses.add(
        responses.GET,
        'https://api.codeclimate.com/v1/repos/123/test_reports',
        json={'data': [{'attributes': {'covered_percent': 99}}]},
    )
    assert code_climate_api.get_test_coverage() == 99
