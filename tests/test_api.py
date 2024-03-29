import datetime
from unittest.mock import patch

import responses
from deal import cases
from hypothesis import given
from hypothesis.provisional import urls
from hypothesis.strategies import builds, lists, text, integers, one_of

from opensource_watchman.api.codeclimate_api import CodeClimateAPI
from opensource_watchman.api.pypistats import get_pypi_downloads_stat
from opensource_watchman.api.travis import TravisRepoAPI
from opensource_watchman.pipelines.extended_repo_info import fetch_downloads_stat
from opensource_watchman.pipelines.github import (
    fetch_last_commit_date, fetch_detailed_pull_requests,
    fetch_ow_repo_config, fetch_badges_urls,
)
from opensource_watchman.pipelines.master import analyze_is_pypi_response_ok


test_travis_extract_commands_from_raw_log = cases(TravisRepoAPI._extract_commands_from_raw_log)


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


def test_fetch_last_commit_date(mocked_responses, github_api):
    mocked_responses.mock_calls([
        (
            'https://api.github.com/repos/test/test/commits',
            [{'commit': {'committer': {'date': '2021-01-23T00:00:00Z'}}}],
        ),
    ])

    assert fetch_last_commit_date(github_api) == datetime.datetime(2021, 1, 23)


def test_fetch_detailed_pull_requests(mocked_responses, github_api):
    mocked_responses.mock_calls([
        (
            'https://api.github.com/repos/test/test/pulls/1',
            {'number': 1, 'id': 123},
        ),
    ])

    actual_result = fetch_detailed_pull_requests(github_api, [{'number': 1}])

    assert actual_result == {1: {'number': 1, 'id': 123}}


def test_fetch_ow_repo_config(mocked_responses, github_api, config_file_name, config_section_name):
    mocked_responses.mock_calls([
        (
            f'https://raw.githubusercontent.com/test/test/master/{config_file_name}',
            '[foo]\na=1\n[ow]\nb=2',
        ),
    ])

    assert fetch_ow_repo_config(github_api, config_file_name, config_section_name) == {'b': '2'}


def test_analyze_is_pypi_response_ok(mocked_responses, github_pipeline_result):
    mocked_responses.mock_calls([
        'https://pypi.org/project/test/',
    ])
    assert analyze_is_pypi_response_ok('test', github_pipeline_result)


@given(
    builds(
        lambda d: ' '.join(d),
        lists(one_of(
            text(),
            urls().map(lambda u: f'![label]({u})'),
        )),
    ),
    integers(),
)
def test_fetch_badges_urls(sample_readme_text, height):
    with patch(
        'opensource_watchman.pipelines.github.get_image_height_in_pixels',
        return_value=height,
    ):
        fetch_badges_urls(sample_readme_text)
