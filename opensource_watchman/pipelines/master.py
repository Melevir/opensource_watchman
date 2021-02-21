import datetime
import operator

import yaml

from requests import get
from typing import List

from opensource_watchman.api.codeclimate_api import CodeClimateAPI
from opensource_watchman.composer import AdvancedComposer
from opensource_watchman.utils.logs_analiser import if_logs_has_any_of_commands


def has_readme(github_data):
    error = (
        f'{github_data["readme_file_name"]} not found'
        if github_data['readme_content'] is None
        else None
    )
    return [error] if error else []


def has_required_sections_in_readme(required_readme_sections, github_data, D01):
    if github_data['ow_repo_config'].get('type') == 'readings' or D01:
        return

    errors: List[str] = []

    for options in required_readme_sections:
        if not any(o in github_data['readme_content'].lower() for o in options):
            errors.append(f'None of following found in readme: {",".join(options)}')
    return errors


def has_ci_config(github_data):
    error = (
        f'{github_data["ci_config_file_name"]} not found'
        if github_data['ci_config_content'] is None
        else None
    )
    return [error] if error else []


def is_ci_bild_status_ok(travis_data, C01):
    errors = []
    if not C01 and travis_data['last_build'] and travis_data['last_build']['state'] != 'passed':
        errors = [f'Current build status on Travis is not ok']
    return errors


def has_all_required_commands_in_build(
    required_commands_to_run_in_build,
    github_data,
    travis_data,
):
    errors: List[str] = []
    for section_info in required_commands_to_run_in_build:
        if not all(p(github_data['ow_repo_config']) for p in section_info['prerequisites']):
            continue

        section = section_info['cmd']
        if not if_logs_has_any_of_commands(travis_data['last_build_commands'], section):
            error_perfix = f'None of {",".join(section)} is' if len(
                section) > 1 else f'{section[0]} is not'
            errors.append(f'{error_perfix} found in build')
    return errors


def has_ci_badge_in_readme(github_data, travis_data):
    errors = []
    if (
        github_data['readme_content']
        and travis_data['badge_url'] not in github_data['readme_content']
    ):
        errors = [f'Travis badge not found in {github_data["readme_file_name"]}']
    return errors


def has_ci_weekly_build_enabled(travis_data, C01):
    errors = ['Travis weekly cron build is not enabled']
    for crontab in travis_data['crontabs_info']:
        if crontab['interval'] == 'weekly':
            errors = []
    return errors if not C01 else []


def has_support_of_python_versions(github_data, C01, required_python_versions):
    repo_config = github_data['ow_repo_config'] or {}
    if 'python' not in repo_config.get('main_languages', '') or C01:
        return

    python_build_versions = yaml.load(
        github_data['ci_config_content'],
        Loader=yaml.FullLoader,
    ).get('python', [])
    errors: List[str] = []
    for required_python_version in required_python_versions:
        if required_python_version not in python_build_versions:
            errors.append(f'Travis build is not running on Python {required_python_version}')
    return errors


def fetch_package_name(
    github_data,
    package_name_path: str,
):
    package_var_name = package_name_path.split(':')[-1]
    file_content = github_data['file_with_package_name_content']
    if file_content is None:
        return {'package_name': None}
    package_name = None
    for line in file_content.splitlines():
        prepared_line = line.split('#')[0].strip().replace(' ', '')
        if prepared_line.startswith(f'{package_var_name}='):
            package_name = prepared_line.split('=')[1].strip("'").strip('"')
    return package_name


def analyze_is_pypi_response_ok(package_name, github_data):
    if (
        github_data['ow_repo_config'].get('type') == 'project'
        and 'python' not in github_data['ow_repo_config'].get('main_languages', '')
    ):
        return

    is_pypi_response_ok = None
    if package_name is not None:
        is_pypi_response_ok = get(f'https://pypi.org/project/{package_name}/').ok
    return is_pypi_response_ok


def has_package_name(package_name, package_name_path, github_data):
    if (
        github_data['ow_repo_config'].get('type') == 'project'
        or 'python' not in github_data['ow_repo_config'].get('main_languages', '')
    ):
        return
    if not package_name:
        return [f'Package name not found at {package_name_path}']


def is_package_on_pypi(is_pypi_response_ok, package_name, github_data):
    if (
        github_data['ow_repo_config'].get('type') == 'project'
        and 'python' not in github_data['ow_repo_config'].get('main_languages', '')
    ):
        return
    if package_name and not is_pypi_response_ok:
        return [f'Package {package_name} is not released at PyPI']


def has_commits_in_last_n_months(github_data, max_age_of_last_commit_in_months):
    delta_days = (datetime.datetime.now() - github_data['last_commit_date']).days
    errors = []
    if delta_days / 30 > max_age_of_last_commit_in_months:
        errors = [
            f'Last commit was at {github_data["last_commit_date"]}, more that '
            f'{max_age_of_last_commit_in_months} months ago',
        ]
    return errors


def fetch_code_climate_repo_id(owner, repo_name, code_climate_api_token):
    cc_api = CodeClimateAPI.create(owner, repo_name, code_climate_api_token)
    return cc_api.code_climate_repo_id


def fetch_test_coverage(owner, repo_name, code_climate_api_token):
    cc_api = CodeClimateAPI.create(owner, repo_name, code_climate_api_token)
    return cc_api.get_test_coverage()


def fetch_code_climate_badge_token(owner, repo_name, code_climate_api_token):
    cc_api = CodeClimateAPI.create(owner, repo_name, code_climate_api_token)
    badge_token = cc_api.get_badge_token()
    return badge_token


def fetch_test_coverage_badge_url(code_climate_badge_token):
    return (
        f'https://api.codeclimate.com/v1/badges/{code_climate_badge_token}/test_coverage'
        if code_climate_badge_token
        else None
    )


def is_project_exists_on_codeclimate(code_climate_repo_id, owner, repo_name, github_data):
    if github_data['ow_repo_config'].get('type') == 'readings':
        return

    errors = []
    if code_climate_repo_id is None:
        errors = [f'{owner}/{repo_name} not found at Codeclimate']
    return errors


def has_test_coverage_info(test_coverage, code_climate_repo_id, owner, repo_name):
    errors = []
    if code_climate_repo_id and test_coverage is None:
        errors = [f'No test coverage info found for {owner}/{repo_name} at Codeclimate']
    return errors


def is_test_coverage_fine(test_coverage, min_test_coverage_percents, github_data):
    if github_data['ow_repo_config'].get('type') == 'readings':
        return

    errors = []
    if test_coverage and test_coverage < min_test_coverage_percents:
        errors = [
            f'Test coverage is too low ({test_coverage:.2f}<{min_test_coverage_percents})',
        ]
    return errors


def is_test_coverage_badge_exists(github_data, test_coverage_badge_url, owner, repo_name):
    errors = []
    readme_content = github_data['readme_content']
    if (
        readme_content
        and test_coverage_badge_url
        and test_coverage_badge_url not in readme_content
    ):
        errors = [
            f'Codeclimate test coverage badge not found at {github_data["readme_file_name"]}',
        ]
    return errors


def fetch_issues_stale_days(github_data):
    issues_stale_days = {}
    for issue in github_data['open_issues']:
        updated_at = datetime.datetime.fromisoformat(issue['updated_at'][:-1])
        stale_for_days = (datetime.datetime.now() - updated_at).days
        if issue['comments']:
            comments = github_data['issues_comments'][issue['number']]
            last_comment_date = datetime.datetime.fromisoformat(
                max(c['updated_at'] for c in comments)[:-1],
            )
            stale_for_days = (datetime.datetime.now() - last_comment_date).days
        issues_stale_days[issue['number']] = stale_for_days
    return issues_stale_days


def has_enough_actual_issues(
    github_data,
    issues_stale_days,
    max_issue_update_age_months,
    min_number_of_actual_issues,
):
    if github_data['ow_repo_config'].get('features_from_contributors_are_welcome') == 'False':
        return

    actual_issues = 0
    for issue in github_data['open_issues']:
        stale_for_days = issues_stale_days[issue['number']]
        if stale_for_days / 30 < max_issue_update_age_months:
            actual_issues += 1
            continue
    errors = []
    if actual_issues < min_number_of_actual_issues:
        errors = [f'Too few actual issues ({actual_issues}<{min_number_of_actual_issues})']
    return errors


def analyze_is_prs_ok_to_merge(github_data):
    is_prs_ok_to_merge = {p['number']: True for p in github_data['open_pull_requests']}
    for pull_request in github_data['open_pull_requests']:
        pr_number = pull_request['number']
        statuses_info = github_data['pull_request_details'][pr_number]['statuses_info']
        if statuses_info and statuses_info[0]['state'] != 'success':
            is_prs_ok_to_merge[pr_number] = False
            continue

        last_review = github_data['pull_request_details'][pr_number]['last_review']
        if last_review and last_review['state'] == 'CHANGES_REQUESTED':
            is_prs_ok_to_merge[pr_number] = False
            continue
    return is_prs_ok_to_merge


def componse_pull_requests_updated_at(github_data):
    pull_requests_updated_at = {p['number']: True for p in github_data['open_pull_requests']}
    for pull_request in github_data['open_pull_requests']:
        pr_number = pull_request['number']
        updated_at = pull_request['updated_at']
        comments = github_data['pull_request_details'][pr_number]['comments']
        last_comment = (
            max(comments, key=operator.itemgetter('updated_at'))
            if comments
            else None
        )
        if last_comment and last_comment['updated_at'] > updated_at:
            updated_at = last_comment['updated_at']
        pull_requests_updated_at[pr_number] = datetime.datetime.fromisoformat(updated_at[:-1])
    return pull_requests_updated_at


def has_no_stale_pull_requests(
    github_data,
    is_prs_ok_to_merge,
    pull_requests_updated_at,
    max_ok_pr_age_days,
):
    errors = []
    for base_pull_request_info in github_data['open_pull_requests']:
        pull_request = github_data['detailed_pull_requests'][base_pull_request_info['number']]
        if is_prs_ok_to_merge[pull_request['number']]:
            updated_at = pull_requests_updated_at[pull_request['number']]
            stale_for_days = (datetime.datetime.now() - updated_at).days
            if stale_for_days > max_ok_pr_age_days:
                errors = [
                    f'Pull request #{pull_request["number"]} is stale '
                    f'for too long ({stale_for_days} days)',
                ]
    return errors


def create_master_pipeline(**kwargs) -> AdvancedComposer:
    pipes = {
        'D01': has_readme,
        'D02': has_required_sections_in_readme,
        'C01': has_ci_config,
        'C02': is_ci_bild_status_ok,
        'C03': has_all_required_commands_in_build,
        'C04': has_ci_badge_in_readme,
        'C05': has_ci_weekly_build_enabled,
        'P01': has_support_of_python_versions,
        'R01': has_package_name,
        'R02': is_package_on_pypi,
        'S01': has_commits_in_last_n_months,
        'T01': is_project_exists_on_codeclimate,
        'T02': has_test_coverage_info,
        'T03': is_test_coverage_fine,
        'T04': is_test_coverage_badge_exists,
        'I01': has_enough_actual_issues,
        'M01': has_no_stale_pull_requests,
    }
    return AdvancedComposer().update_parameters(**kwargs).update_without_prefix(
        'fetch_',
        fetch_code_climate_repo_id,
        fetch_test_coverage,
        fetch_code_climate_badge_token,
        fetch_test_coverage_badge_url,
        fetch_issues_stale_days,
        fetch_package_name,
    ).update_without_prefix(
        'analyze_',
        analyze_is_prs_ok_to_merge,
        analyze_is_pypi_response_ok,
    ).update_without_prefix(
        'componse_',
        componse_pull_requests_updated_at,
    ).update(**pipes)
