import deal

from opensource_watchman.pipelines.github import (
    create_api, fetch_project_description, create_github_pipeline, fetch_pull_request_details,
)
from opensource_watchman.pipelines.master import (
    has_readme, has_required_sections_in_readme,
    has_ci_config, is_ci_bild_status_ok, has_ci_badge_in_readme, has_ci_weekly_build_enabled,
    has_support_of_python_versions, fetch_package_name, has_package_name, is_package_on_pypi,
    has_commits_in_last_n_months, fetch_test_coverage_badge_url, is_project_exists_on_codeclimate,
    has_test_coverage_info, is_test_coverage_fine, is_test_coverage_badge_exists,
    fetch_issues_stale_days, has_enough_actual_issues, analyze_is_prs_ok_to_merge,
    compose_pull_requests_updated_at, has_no_stale_pull_requests, create_master_pipeline,
)
from opensource_watchman.pipelines.travis import create_travis_pipeline
from opensource_watchman.utils.test_strategies import cases


test_github_create_api = cases(create_api)
test_github_fetch_project_description = cases(fetch_project_description)
test_create_github_pipeline = cases(create_github_pipeline)
test_create_travis_pipeline = cases(create_travis_pipeline)
test_master_has_readme = cases(has_readme)
test_master_has_required_sections_in_readme = cases(has_required_sections_in_readme)
test_master_has_ci_config = cases(has_ci_config)
test_master_is_ci_bild_status_ok = cases(is_ci_bild_status_ok)
test_master_has_ci_badge_in_readme = cases(has_ci_badge_in_readme)
test_master_has_ci_weekly_build_enabled = cases(has_ci_weekly_build_enabled)
test_master_fetch_package_name = cases(fetch_package_name)
test_master_has_package_name = cases(has_package_name)
test_master_is_package_on_pypi = cases(is_package_on_pypi)
test_master_has_commits_in_last_n_months = cases(has_commits_in_last_n_months)
test_master_fetch_test_coverage_badge_url = cases(fetch_test_coverage_badge_url)
test_master_is_project_exists_on_codeclimate = cases(is_project_exists_on_codeclimate)
test_master_has_test_coverage_info = cases(has_test_coverage_info)
test_master_is_test_coverage_fine = cases(is_test_coverage_fine)
test_master_is_test_coverage_badge_exists = cases(is_test_coverage_badge_exists)
test_master_fetch_issues_stale_days = cases(fetch_issues_stale_days)
test_master_has_enough_actual_issues = cases(has_enough_actual_issues)
test_master_analyze_is_prs_ok_to_merge = cases(analyze_is_prs_ok_to_merge)
test_master_compose_pull_requests_updated_at = cases(compose_pull_requests_updated_at)
test_master_has_no_stale_pull_requests = cases(has_no_stale_pull_requests)
test_master_create_master_pipeline = cases(create_master_pipeline)
test_master_has_support_of_python_versions = cases(has_support_of_python_versions)


def test_fetch_pull_request_details(github_api, detailed_pull_requests, mocked_responses):
    mocked_responses.mock_calls([
        ('https://api.github.com/repos/test/test/pulls/1/commits', [{'sha': '123123'}]),
        'https://api.github.com/repos/test/test/commits/123123/statuses',
        'https://api.github.com/repos/test/test/commits/123123/reviews',
        'https://api.github.com/repos/test/test/pulls/1/comments',
    ])

    actual_result = fetch_pull_request_details(github_api, detailed_pull_requests)

    assert actual_result == {
        1: {
            'last_commit_sha': '123123',
            'statuses_info': [],
            'last_review': None,
            'comments': [],
        },
    }
