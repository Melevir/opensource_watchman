import deal

from opensource_watchman.pipelines.github import (
    create_api, fetch_project_description, create_github_pipeline,
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


test_github_create_api = deal.cases(create_api)
test_github_fetch_project_description = deal.cases(fetch_project_description)
test_create_github_pipeline = deal.cases(create_github_pipeline)
test_create_travis_pipeline = deal.cases(create_travis_pipeline)
test_master_has_readme = deal.cases(has_readme)
test_master_has_required_sections_in_readme = deal.cases(has_required_sections_in_readme)
test_master_has_ci_config = deal.cases(has_ci_config)
test_master_is_ci_bild_status_ok = deal.cases(is_ci_bild_status_ok)
test_master_has_ci_badge_in_readme = deal.cases(has_ci_badge_in_readme)
test_master_has_ci_weekly_build_enabled = deal.cases(has_ci_weekly_build_enabled)
test_master_has_support_of_python_versions = deal.cases(has_support_of_python_versions)
test_master_fetch_package_name = deal.cases(fetch_package_name)
test_master_has_package_name = deal.cases(has_package_name)
test_master_is_package_on_pypi = deal.cases(is_package_on_pypi)
test_master_has_commits_in_last_n_months = deal.cases(has_commits_in_last_n_months)
test_master_fetch_test_coverage_badge_url = deal.cases(fetch_test_coverage_badge_url)
test_master_is_project_exists_on_codeclimate = deal.cases(is_project_exists_on_codeclimate)
test_master_has_test_coverage_info = deal.cases(has_test_coverage_info)
test_master_is_test_coverage_fine = deal.cases(is_test_coverage_fine)
test_master_is_test_coverage_badge_exists = deal.cases(is_test_coverage_badge_exists)
test_master_fetch_issues_stale_days = deal.cases(fetch_issues_stale_days)
test_master_has_enough_actual_issues = deal.cases(has_enough_actual_issues)
test_master_analyze_is_prs_ok_to_merge = deal.cases(analyze_is_prs_ok_to_merge)
test_master_compose_pull_requests_updated_at = deal.cases(compose_pull_requests_updated_at)
test_master_has_no_stale_pull_requests = deal.cases(has_no_stale_pull_requests)
test_master_create_master_pipeline = deal.cases(create_master_pipeline)
