import deal
import responses

from opensource_watchman.api.pypistats import get_pypi_downloads_stat
from opensource_watchman.api.travis import TravisRepoAPI
from opensource_watchman.pipelines.extended_repo_info import fetch_downloads_stat

test_travis_extract_commands_from_raw_log = deal.cases(TravisRepoAPI._extract_commands_from_raw_log)


def test_get_pypi_stats(mocked_responses):
    test_project_name = 'test'
    mocked_responses.add(
        responses.GET,
        f'https://pypistats.org/api/packages/{test_project_name}/recent',
        json={"data": {"last_week": 1}},
    )

    assert get_pypi_downloads_stat(test_project_name)['last_week'] == 1


def test_fetch_downloads_stat(ok_repo_result, mocked_responses):
    mocked_responses.add(
        responses.GET,
        'https://pypistats.org/api/packages/test/recent',
        json={"data": {"last_week": 1}},
    )
    assert fetch_downloads_stat([ok_repo_result]) == {'test_repo': 1}
