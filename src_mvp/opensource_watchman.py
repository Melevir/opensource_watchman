import collections
import functools
import datetime
import io
import operator
import os
import re
from typing import List, Callable, Tuple, Optional, Mapping, Any

from colored import fg, attr
import requests
import yaml
from PIL import Image, UnidentifiedImageError
from requests import get

from codeclimate_api import get_repo_id, get_test_coverage, get_badge_token
from github_api import get_repos_list, get_file_contents, get_repo_info, get_last_commit_date, \
    get_open_issues, get_issue_comments, get_open_pull_requests, is_pull_request_ok_to_merge, \
    get_pull_request_updated_at, get_pull_request_info, get_project_description, get_repo_config
from hh_api import filter_vacancies, get_actual_vacancies
from prerequisites import python_only, rus_only
from pypistats_api import get_pypi_downloads_stat
from renderers import render_html_report
from travis_api import get_last_build_commands, is_last_build_passed, get_crontabs_info


def validate_repo(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    validators: List[Callable],
) -> List[Tuple[str, str]]:
    errors: List[Tuple[str, str]] = []
    for validator in validators:
        errors += validator(
            owner=owner,
            repo_name=repo_name,
            repo_config=repo_config,
        )
    return errors


def has_required_sections_in_readme(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    readme_file_name: str,
) -> List[Tuple[str, str]]:
    required_sections = [
        ['installation'],
        ['contributing', 'contribution'],
        ['usage', 'example', 'sample'],
    ]

    if repo_config.get('type') == 'readings':
        return []

    readme_content = get_file_contents(owner, repo_name, readme_file_name)
    if readme_content is None:
        return [('D01', f'{readme_file_name} not found')]
    readme_content = readme_content.lower()

    errors: List[Tuple[str, str]] = []
    for options in required_sections:
        if not any(o in readme_content for o in options):
            errors.append(
                ('D02', f'None of following found in readme: {",".join(options)}'),
            )
    return errors


def has_propper_ci(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    travis_config_filename: str,
    readme_file_name: str,
    required_commands_to_run_in_build: List[str],
) -> List[Tuple[str, str]]:
    travis_config_contents = get_file_contents(owner, repo_name, travis_config_filename)
    if travis_config_contents is None:
        return [('C01', f'{travis_config_filename} not found')]

    if not is_last_build_passed(owner, repo_name):
        return [('C02', f'Current build status on Travis is not ok')]
    executed_commands = get_last_build_commands(owner, repo_name)

    errors: List[Tuple[str, str]] = []
    for section_info in required_commands_to_run_in_build:
        if not all(p(repo_config) for p in section_info['prerequisites']):
            continue

        section = section_info['cmd']
        is_section_present = False
        for required_command in section:
            for base_command in executed_commands:
                if (
                    base_command.startswith(f'{required_command} ')
                    or f' {required_command} ' in base_command
                    or base_command == required_command
                ):
                    is_section_present = True
                    break
        if not is_section_present:
            error_perfix = f'None of {",".join(section)} is' if len(section) > 1 else f'{section[0]} is not'
            errors.append(
                ('C03', f'{error_perfix} found in build')
            )

    travis_build_label_url = f'https://travis-ci.org/{owner}/{repo_name}.svg'
    readme_content = get_file_contents(owner, repo_name, readme_file_name)
    if readme_content and travis_build_label_url not in readme_content:
        errors.append(
            ('C04', f'Travis badge not found in {readme_file_name}'),
        )

    is_crontab_ok = False
    crontabs_info = get_crontabs_info(owner, repo_name)
    for crontab in crontabs_info:
        if crontab['interval'] == 'weekly':
            is_crontab_ok = True
    if not is_crontab_ok:
        errors.append(
            ('C05', f'Travis weekly cron build is not enabled'),
        )
    return errors


def has_support_of_python_versions(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    travis_config_filename: str,
    versions: List[str],
) -> List[Tuple[str, str]]:
    if 'python' not in repo_config.get('main_languages', ''):
        return []

    travis_config_contents = get_file_contents(owner, repo_name, travis_config_filename)
    if travis_config_contents is None:
        return [('C01', f'{travis_config_filename} not found')]
    python_build_versions = yaml.load(travis_config_contents, Loader=yaml.FullLoader).get('python', [])
    errors: List[Tuple[str, str]] = []
    for required_python_version in versions:
        if required_python_version not in python_build_versions:
            errors.append(
                ('P01', f'Travis build is not running on Python {required_python_version}')
            )
    return errors


def get_pypi_project_name(
    owner: str,
    repo_name: str,
    package_name_path: str,
) -> Optional[str]:
    package_file, package_var_name = package_name_path.split(':')
    file_content = get_file_contents(owner, repo_name, package_file)
    if file_content is None:
        return None
    package_name = None
    for line in file_content.splitlines():
        prepared_line = line.split('#')[0].strip().replace(' ', '')
        if prepared_line.startswith(f'{package_var_name}='):
            package_name = prepared_line.split('=')[1].strip("'").strip('"')
    return package_name


def has_pypi_release(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    package_name_path: str,
) -> List[Tuple[str, str]]:
    if repo_config.get('type') == 'project' or 'python' not in repo_config.get('main_languages', ''):
        return []

    package_name = get_pypi_project_name(owner, repo_name, package_name_path)
    if package_name is None:
        return [('R01', f'Package name not found at {package_name_path}')]
    if not requests.get(f'https://pypi.org/project/{package_name}/'):
        return [('R02', f'Package {package_name} is not released at PyPI')]
    return []


def has_commits_in_last_n_months(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    n_months: int,
) -> List[Tuple[str, str]]:
    last_commit_date = get_last_commit_date(owner, repo_name)
    delta_days = (datetime.datetime.now() - last_commit_date).days
    if delta_days / 30 > n_months:
        return [('S01', f'Last commit was at {last_commit_date}, more that {n_months} months ago')]
    return []


def has_min_test_coverage(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    min_test_coverage_percents: int,
    readme_file_name: str,
) -> List[Tuple[str, str]]:
    if repo_config.get('type') == 'readings':
        return []

    codeclimate_repo_id = get_repo_id(owner, repo_name)
    if codeclimate_repo_id is None:
        return [('T01', f'{owner}/{repo_name} not found at Codeclimate')]
    test_coverage = get_test_coverage(codeclimate_repo_id)
    if test_coverage is None:
        return [('T02', f'No test coverage info found for {owner}/{repo_name} at Codeclimate')]
    errors: List[Tuple[str, str]] = []
    if test_coverage < min_test_coverage_percents:
        errors.append(
            ('T03', f'Test coverage is too low ({test_coverage:.2f}<{min_test_coverage_percents})'),
        )

    readme_content = get_file_contents(owner, repo_name, readme_file_name)
    badge_token = get_badge_token(owner, repo_name)
    test_coverage_badge_url = f'https://api.codeclimate.com/v1/badges/{badge_token}/test_coverage'
    if readme_content and test_coverage_badge_url not in readme_content:
        errors.append(
            ('T04', f'Codeclimate test coverage badge not found at {readme_file_name}'),
        )

    return errors


def has_no_mess_with_issues(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    min_number_of_actual_issues: int,
    max_issue_update_age_months: int,
) -> List[Tuple[str, str]]:
    if repo_config.get('features_from_contributors_are_welcome') == 'False':
        return []

    issues = get_open_issues(owner, repo_name)
    actual_issues = 0
    for issue in issues:
        updated_at = datetime.datetime.fromisoformat(issue['updated_at'][:-1])
        stale_for_days = (datetime.datetime.now() - updated_at).days
        if stale_for_days / 30 < max_issue_update_age_months:
            actual_issues += 1
            continue
        if issue['comments']:
            comments = get_issue_comments(owner, repo_name, issue['number'])
            last_comment_date = datetime.datetime.fromisoformat(
                max(c['updated_at'] for c in comments)[:-1],
            )
            stale_for_days = (datetime.datetime.now() - last_comment_date).days
            if stale_for_days / 30 < max_issue_update_age_months:
                actual_issues += 1
                continue
    if actual_issues < min_number_of_actual_issues:
        return [('I01', f'Too few actual issues ({actual_issues}<{min_number_of_actual_issues})')]
    return []


def has_no_pending_pull_requests(
    owner: str,
    repo_name: str,
    repo_config: Mapping[str, Any],
    max_ok_pr_age_days: int,
) -> List[Tuple[str, str]]:
    for base_pull_request_info in get_open_pull_requests(owner, repo_name):
        pull_request = get_pull_request_info(owner, repo_name, base_pull_request_info['number'])
        if is_pull_request_ok_to_merge(pull_request):
            updated_at = get_pull_request_updated_at(pull_request)
            stale_for_days = (datetime.datetime.now() - updated_at).days
            if stale_for_days > max_ok_pr_age_days:
                return [
                    (
                        'M01',
                        f'Pull request #{pull_request["number"]} is stale '
                        f'for too long ({stale_for_days} days)',
                    ),
                ]
    return []


def extract_badges(owner: str, repo_name: str, readme_file_name: str) -> List[str]:
    readme_content = get_file_contents(owner, repo_name, readme_file_name)
    if readme_content is None:
        return []
    image_urls = re.findall(r'(?:!\[.*?\]\((.*?)\))', readme_content)
    badges_urls = []
    for url in image_urls:
        # print(url)
        img_data = get(url).content
        # print(img_data)
        try:
            im = Image.open(io.BytesIO(img_data))
        except UnidentifiedImageError:  # this happens with svg, should parse it and get height
            badges_urls.append(url)
            continue
        height = im.size[1]
        if height < 60:
            badges_urls.append(url)
    return badges_urls


def get_last_week_downloads(owner: str, repo_name: str, package_name_path: str) -> Optional[int]:
    package_name = get_pypi_project_name(owner, repo_name, package_name_path)
    if package_name:
        pypi_stat = get_pypi_downloads_stat(package_name)
        return pypi_stat.get('last_week') if pypi_stat else None


def get_repo_status(errors_info: List[Tuple[str, str, str]]) -> str:
    if not errors_info:
        return 'ok'
    severities = {e[2] for e in errors_info}
    return 'critical' if 'critical' in severities else 'warning'


def get_total_stat(repos_context, repos_to_skip):
    return {
        'checked_repos_number': len(repos_context),
        'skipped_repos_number': len(repos_to_skip),
        'total_repos_number': len(repos_context) + len(repos_to_skip),
        'ok_repos_number': sum(1 for r in repos_context.values() if r['status'] == 'ok'),
        'repos_with_warnings_number': sum(1 for r in repos_context.values() if r['status'] == 'warning'),
        'critical_repos_number': sum(1 for r in repos_context.values() if r['status'] == 'critical'),
    }


if __name__ == '__main__':
    travis_config_filename = '.travis.yml'
    readme_file_name = 'README.md'
    package_name_path = 'setup.py:package_name'
    config_file_name = 'setup.cfg'
    config_section_name = 'opensource_watchman'

    errors_severity = {
        'D01': 'critical',
        'D02': 'warning',
        'C01': 'critical',
        'C02': 'critical',
        'C03': 'warning',
        'C04': 'warning',
        'C05': 'critical',
        'P01': 'warning',
        'R01': 'warning',
        'R02': 'critical',
        'S01': 'critical',
        'T01': 'critical',
        'T02': 'critical',
        'T03': 'warning',
        'T04': 'warning',
        'I01': 'warning',
        'M01': 'critical',
    }
    severity_colors = {
        'warning': fg(3),
        'critical': fg(1),
    }
    it_vacancies_triggers = [
        'python',
        'ios',
        'android',
        'data',
        'js',
        'бекенд',
        'фронтенд',
        'инженер',
    ]

    hh_employer_id = os.environ.get('HH_EMPLOYER_ID')
    owner = 'best-doctor'
    # repos = ['its_on']
    repos = get_repos_list(owner)
    repos_to_skip = {}
    repos = [r for r in repos if r not in repos_to_skip]
    repos_context = collections.defaultdict(dict)
    ok_repos_number = 0
    for repo_name in repos:
        print(repo_name)
        repo_config = get_repo_config(owner, repo_name, config_file_name, config_section_name)
        repo_info = get_repo_info(owner, repo_name)
        if repo_info and repo_info['archived']:
            print('\tarchived')
            continue
        errors = validate_repo(
            owner=owner,
            repo_name=repo_name,
            repo_config=repo_config,
            validators=[
                functools.partial(has_required_sections_in_readme, readme_file_name=readme_file_name),
                functools.partial(
                    has_propper_ci,
                    travis_config_filename=travis_config_filename,
                    readme_file_name=readme_file_name,
                    required_commands_to_run_in_build=[
                        {'prerequisites': [python_only], 'cmd': ['flake8']},
                        {'prerequisites': [python_only], 'cmd': ['mypy']},
                        {'prerequisites': [python_only], 'cmd': ['pytest', 'py.test', 'python -m pytest']},
                        {'prerequisites': [], 'cmd': ['mdl']},
                        {'prerequisites': [python_only], 'cmd': ['safety']},
                        {'prerequisites': [rus_only], 'cmd': ['rozental']},
                    ],
                ),
                functools.partial(
                    has_support_of_python_versions,
                    travis_config_filename=travis_config_filename,
                    versions=['3.7', '3.8'],
                ),
                functools.partial(
                    has_pypi_release,
                    package_name_path=package_name_path,
                ),
                functools.partial(
                    has_commits_in_last_n_months,
                    n_months=6,
                ),
                functools.partial(
                    has_min_test_coverage,
                    min_test_coverage_percents=80,
                    readme_file_name=readme_file_name,
                ),
                functools.partial(
                    has_no_mess_with_issues,
                    min_number_of_actual_issues=3,
                    max_issue_update_age_months=6,
                ),
                functools.partial(
                    has_no_pending_pull_requests,
                    max_ok_pr_age_days=7,
                ),
                # TODO:
                # - **Код может лежать на Гитхабе, но не быть зарелижен не больше 2 недель.**
                # - **На свежесозданные задачи мы отвечаем в течение 14 дней.**
            ],
        )
        repos_context[repo_name]['errors'] = sorted(
            [(c, e, errors_severity[c]) for (c, e) in list(set(errors))],
            key=operator.itemgetter(2),
        )
        repos_context[repo_name]['status'] = get_repo_status(repos_context[repo_name]['errors'])
        repos_context[repo_name]['badges'] = extract_badges(owner, repo_name, readme_file_name)
        repos_context[repo_name]['downloads_last_week'] = get_last_week_downloads(owner, repo_name, package_name_path)
        repos_context[repo_name]['description'] = get_project_description(owner, repo_name)

        for error_slug, error_text in sorted(list(set(errors))):
            error_color = severity_colors[errors_severity[error_slug]]
            print(f'\t{error_color}{error_slug}: {error_text}{attr(0)}')
        if not errors:
            ok_repos_number += 1
            print(f'\t{fg(2)}ok{attr(0)}')

    ok_repos_percent = ok_repos_number / len(repos) * 100
    print(f'{ok_repos_percent:.2f}% of all repos are ok ({ok_repos_number} of {len(repos)})')
    repos_context = dict(repos_context)
    print(repos_context)

    context = {
        'owner': owner,
        'repos': sorted(repos_context.items(), key=lambda r: len(r[1]['errors'])),
        'skip': repos_to_skip,
        'total': get_total_stat(repos_context, repos_to_skip),
        'severity_colors': {'ok': 'green', 'warning': 'yellow', 'critical': 'red'},
        'actual_vacancies': filter_vacancies(
            get_actual_vacancies(hh_employer_id=hh_employer_id),
            triggers=it_vacancies_triggers,
        )
    }

    render_html_report(
        context,
        template_file_name='report_template.html',
        result_file='report.html',
    )
