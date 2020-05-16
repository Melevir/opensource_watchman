import json
import logging
import operator
import os
from typing import Optional, List

from click import command, option, argument, Choice

from opensource_watchman.common_types import RepoResult, OpensourceWatchmanConfig
from opensource_watchman.config import DEFAULT_HTML_REPORT_FILE_NAME
from opensource_watchman.output_processors import print_errors_data, prepare_html_report
from opensource_watchman.pipelines.github import GithubReceiveDataPipeline
from opensource_watchman.pipelines.travis import TravisReceiveDataPipeline
from opensource_watchman.pipelines.master import MasterPipeline
from opensource_watchman.prerequisites import python_only, rus_only
from opensource_watchman.api.github import GithubRepoAPI


logger = logging.getLogger('super_mario')
logger.setLevel(logging.DEBUG)


def load_config() -> OpensourceWatchmanConfig:
    return OpensourceWatchmanConfig(
        config_file_name='setup.cfg',
        config_section_name='opensource_watchman',
        readme_file_name='README.md',
        ci_config_file_name='.travis.yml',
        package_name_path='setup.py:package_name',
        github_login=os.environ['GITHUB_USERNAME'],
        github_api_token=os.environ['GITHUB_API_TOKEN'],
        travis_api_login=os.environ['TRAVIS_CI_ORG_ACCESS_TOKEN'],
        required_readme_sections=[
            ['installation'],
            ['contributing', 'contribution'],
            ['usage', 'example'],
        ],
        required_commands_to_run_in_build=[
            {'prerequisites': [python_only], 'cmd': ['flake8']},
            {'prerequisites': [python_only], 'cmd': ['mypy']},
            {'prerequisites': [python_only], 'cmd': ['pytest', 'py.test', 'python -m pytest']},
            {'prerequisites': [], 'cmd': ['mdl']},
            {'prerequisites': [python_only], 'cmd': ['safety']},
            {'prerequisites': [rus_only], 'cmd': ['rozental']},
        ],
        required_python_versions=['3.7', '3.8'],
        max_age_of_last_commit_in_months=6,
        code_climate_api_token=os.environ['CODECLIMATE_API_TOKEN'],
        min_test_coverage_percents=80,
        min_number_of_actual_issues=3,
        max_issue_update_age_months=6,
        max_ok_pr_age_days=7,
    )


def get_repos_names(owner, github_login, github_token, skip_archived):
    repos = GithubRepoAPI(owner, None, github_login, github_token).fetch_repos_list() or []
    if skip_archived:
        repos = [r for r in repos if not r['archived']]
    repos.sort(key=operator.itemgetter('updated_at'))
    return [r['name'] for r in reversed(repos)]


def run_watchman(
    owner: str,
    repo_name: Optional[str],
    exclude_list: List[str],
    config,
) -> List[RepoResult]:
    repos_info = []

    repos_to_process = (
        [repo_name]
        if repo_name else
        [
            r for r in get_repos_names(
                owner,
                config.github_login,
                config.github_api_token,
                skip_archived=True,
            )
            if r not in exclude_list
        ]
    )
    for repo_to_process in repos_to_process:
        github_pipeline = GithubReceiveDataPipeline()
        github_pipeline.run(
            owner=owner,
            repo_name=repo_to_process,
            config_file_name=config.config_file_name,
            config_section_name=config.config_section_name,
            readme_file_name=config.readme_file_name,
            ci_config_file_name=config.ci_config_file_name,
            package_name_path=config.package_name_path,
            github_login=config.github_login,
            github_api_token=config.github_api_token,
        )
        travis_pipeline = TravisReceiveDataPipeline()
        travis_pipeline.run(
            owner=owner,
            repo_name=repo_to_process,
            travis_api_login=config.travis_api_login,
        )

        pipeline = MasterPipeline()
        pipeline.run(
            owner=owner,
            repo_name=repo_to_process,
            package_name_path=config.package_name_path,
            github_data=github_pipeline.__context__,
            travis_data=travis_pipeline.__context__,
            required_readme_sections=config.required_readme_sections,
            required_commands_to_run_in_build=config.required_commands_to_run_in_build,
            required_python_versions=config.required_python_versions,
            max_age_of_last_commit_in_months=config.max_age_of_last_commit_in_months,
            code_climate_api_token=config.code_climate_api_token,
            min_test_coverage_percents=config.min_test_coverage_percents,
            min_number_of_actual_issues=config.min_number_of_actual_issues,
            max_issue_update_age_months=config.max_issue_update_age_months,
            max_ok_pr_age_days=config.max_ok_pr_age_days,
        )

        errors_info = {c: e for (c, e) in pipeline.__context__.items() if len(c) == 3 and e}
        repos_info.append(RepoResult(
            owner=owner,
            package_name=pipeline.__context__['package_name'],
            description=github_pipeline.__context__['project_description'],
            badges_urls=github_pipeline.__context__['badges_urls'],
            repo_name=repo_to_process,
            errors=errors_info,
        ))
    return repos_info


def process_results(
    owner: str,
    repos_stat: List[RepoResult],
    output_type: str,
    html_template_path: Optional[str],
    extra_context_provider_py_name: Optional[str],
    result_filename: Optional[str],
    config,
):
    if output_type == 'term':
        print_errors_data(repos_stat)
    elif output_type == 'json':
        print(json.dumps(repos_stat))  # noqa: T001
    elif output_type == 'html' and html_template_path:
        prepare_html_report(
            owner=owner,
            repos_stat=repos_stat,
            html_template_path=html_template_path,
            extra_context_provider_py_name=extra_context_provider_py_name,
            result_filename=result_filename or DEFAULT_HTML_REPORT_FILE_NAME,
            config=config,
        )


@command()
@argument('owner')
@option('--repo_name', help='name of exact repo to check')
@option('--config_path', help='path to cfg file')
@option('--skip', 'exclude_list', help='list of validators to skip', multiple=True)
@option(
    '--output_type', help='output format', type=Choice(['term', 'json', 'html']), default='term')
@option('--html_template_path', help='path to result html jinja template to render')
@option(
    '--extra_context_provider_py_name',
    help='importable path of callable, that provides additional context for html template',
)
@option('--result_filename', help='result filename')
def main(
    owner: str,
    repo_name: Optional[str],
    config_path: Optional[str],
    exclude_list: List[str],
    output_type: str,
    html_template_path: Optional[str],
    extra_context_provider_py_name: Optional[str],
    result_filename: Optional[str],
):
    """Run opensource watchman"""
    config = load_config()
    repos_stat = run_watchman(owner, repo_name, exclude_list, config)
    default_template_path = os.path.join(
        os.path.dirname(__file__),
        'templates',
        'report_template.html',
    )
    html_template_path = html_template_path or default_template_path
    process_results(
        owner,
        repos_stat,
        output_type,
        html_template_path,
        extra_context_provider_py_name,
        result_filename,
        config,
    )


if __name__ == '__main__':
    main()
