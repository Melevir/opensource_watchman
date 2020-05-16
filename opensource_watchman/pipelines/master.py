import datetime
import operator

import yaml
from opensource_watchman.pipelines.github import GithubReceiveDataPipeline

from requests import get
from super_mario import process_pipe, BasePipeline, input_pipe
from typing import List

from opensource_watchman.api.codeclimate_api import CodeClimateAPI
from opensource_watchman.utils.logs_analiser import if_logs_has_any_of_commands


class MasterPipeline(BasePipeline):
    pipeline = [
        'has_readme',
        'has_required_sections_in_readme',
        'has_ci_config',
        'is_ci_bild_status_ok',
        'has_all_required_commands_in_build',
        'has_ci_badge_in_readme',
        'has_ci_weekly_build_enabled',
        'has_support_of_python_versions',
        'get_pypi_project_name',
        'check_is_package_exists_at_pypi',
        'has_package_name',
        'is_package_on_pypi',
        'has_commits_in_last_n_months',
        'fetch_codeclimate_info',
        'is_project_exists_on_codeclimate',
        'has_test_coverage_info',
        'is_test_coverage_fine',
        'is_test_coverage_badge_exists',
        'calclulate_issues_stale_time',
        'has_enough_actual_issues',
        'analyze_if_pull_requests_are_ok_to_merge',
        'calculate_pull_requests_updated_at',
        'has_no_stale_pull_requests',
    ]

    @process_pipe
    @staticmethod
    def has_readme(github_data: GithubReceiveDataPipeline):
        error = (
            f'{github_data["readme_file_name"]} not found'
            if github_data['readme_content'] is None
            else None
        )
        return {'D01': [error] if error else []}

    @process_pipe
    @staticmethod
    def has_required_sections_in_readme(required_readme_sections, github_data, D01):
        if github_data['ow_repo_config'].get('type') == 'readings' or D01:
            return

        errors: List[str] = []

        for options in required_readme_sections:
            if not any(o in github_data['readme_content'].lower() for o in options):
                errors.append(f'None of following found in readme: {",".join(options)}')
        return {'D02': errors}

    @process_pipe
    @staticmethod
    def has_ci_config(github_data):
        error = (
            f'{github_data["ci_config_file_name"]} not found'
            if github_data['ci_config_content'] is None
            else None
        )
        return {'C01': [error] if error else []}

    @process_pipe
    @staticmethod
    def is_ci_bild_status_ok(travis_data, C01):
        errors = []
        if not C01 and travis_data['last_build'] and travis_data['last_build']['state'] != 'passed':
            errors = [f'Current build status on Travis is not ok']
        return {'C02': errors}

    @process_pipe
    @staticmethod
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
        return {'C03': errors}

    @process_pipe
    @staticmethod
    def has_ci_badge_in_readme(github_data, travis_data):
        errors = []
        if (
            github_data['readme_content']
            and travis_data['badge_url'] not in github_data['readme_content']
        ):
            errors = [f'Travis badge not found in {github_data["readme_file_name"]}']
        return {'C04': errors}

    @process_pipe
    @staticmethod
    def has_ci_weekly_build_enabled(travis_data, C01):
        errors = ['Travis weekly cron build is not enabled']
        for crontab in travis_data['crontabs_info']:
            if crontab['interval'] == 'weekly':
                errors = []
        return {'C05': errors if not C01 else []}

    @process_pipe
    @staticmethod
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
        return {'P01': errors}

    @process_pipe
    @staticmethod
    def get_pypi_project_name(
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
        return {'package_name': package_name}

    @input_pipe
    @staticmethod
    def check_is_package_exists_at_pypi(package_name, github_data):
        if (
            github_data['ow_repo_config'].get('type') == 'project'
            and 'python' not in github_data['ow_repo_config'].get('main_languages', '')
        ):
            return {'is_pypi_response_ok': None}

        is_pypi_response_ok = None
        if package_name is not None:
            is_pypi_response_ok = get(f'https://pypi.org/project/{package_name}/').ok
        return {'is_pypi_response_ok': is_pypi_response_ok}

    @process_pipe
    @staticmethod
    def has_package_name(package_name, package_name_path, github_data):
        if (
            github_data['ow_repo_config'].get('type') == 'project'
            or 'python' not in github_data['ow_repo_config'].get('main_languages', '')
        ):
            return
        if not package_name:
            return {'R01': [f'Package name not found at {package_name_path}']}

    @process_pipe
    @staticmethod
    def is_package_on_pypi(is_pypi_response_ok, package_name, github_data):
        if (
            github_data['ow_repo_config'].get('type') == 'project'
            and 'python' not in github_data['ow_repo_config'].get('main_languages', '')
        ):
            return
        if package_name and not is_pypi_response_ok:
            return {'R02': [f'Package {package_name} is not released at PyPI']}

    @process_pipe
    @staticmethod
    def has_commits_in_last_n_months(github_data, max_age_of_last_commit_in_months):
        delta_days = (datetime.datetime.now() - github_data['last_commit_date']).days
        errors = []
        if delta_days / 30 > max_age_of_last_commit_in_months:
            errors = [
                f'Last commit was at {github_data["last_commit_date"]}, more that '
                f'{max_age_of_last_commit_in_months} months ago',
            ]
        return {'S01': errors}

    @input_pipe
    @staticmethod
    def fetch_codeclimate_info(owner, repo_name, code_climate_api_token):
        cc_api = CodeClimateAPI.create(owner, repo_name, code_climate_api_token)
        badge_token = cc_api.get_badge_token()
        badge_url = (
            f'https://api.codeclimate.com/v1/badges/{badge_token}/test_coverage'
            if badge_token
            else None
        )
        return {
            'code_climate_repo_id': cc_api.code_climate_repo_id,
            'test_coverage': cc_api.get_test_coverage(),
            'code_climate_badge_token': badge_token,
            'test_coverage_badge_url': badge_url,

        }

    @process_pipe
    @staticmethod
    def is_project_exists_on_codeclimate(code_climate_repo_id, owner, repo_name, github_data):
        if github_data['ow_repo_config'].get('type') == 'readings':
            return

        errors = []
        if code_climate_repo_id is None:
            errors = [f'{owner}/{repo_name} not found at Codeclimate']
        return {'T01': errors}

    @process_pipe
    @staticmethod
    def has_test_coverage_info(test_coverage, code_climate_repo_id, owner, repo_name):
        errors = []
        if code_climate_repo_id and test_coverage is None:
            errors = [f'No test coverage info found for {owner}/{repo_name} at Codeclimate']
        return {'T02': errors}

    @process_pipe
    @staticmethod
    def is_test_coverage_fine(test_coverage, min_test_coverage_percents, github_data):
        if github_data['ow_repo_config'].get('type') == 'readings':
            return

        errors = []
        if test_coverage and test_coverage < min_test_coverage_percents:
            errors = [
                f'Test coverage is too low ({test_coverage:.2f}<{min_test_coverage_percents})',
            ]
        return {'T03': errors}

    @process_pipe
    @staticmethod
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
        return {'T04': errors}

    @process_pipe
    @staticmethod
    def calclulate_issues_stale_time(github_data):
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
        return {'issues_stale_days': issues_stale_days}

    @process_pipe
    @staticmethod
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
        return {'I01': errors}

    @process_pipe
    @staticmethod
    def analyze_if_pull_requests_are_ok_to_merge(github_data):
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
        return {'is_prs_ok_to_merge': is_prs_ok_to_merge}

    @process_pipe
    @staticmethod
    def calculate_pull_requests_updated_at(github_data):
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
        return {'pull_requests_updated_at': pull_requests_updated_at}

    @process_pipe
    @staticmethod
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
        return {'M01': errors}
