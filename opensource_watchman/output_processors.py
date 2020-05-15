from typing import Any, Mapping, List

from colored import fg, attr
from jinja2 import Template

from opensource_watchman.pipelines.extended_repo_info import fetch_downloads_stat
from opensource_watchman.common_types import RepoResult
from opensource_watchman.config import SEVERITY_COLORS, ERRORS_SEVERITY


def print_errors_data(repos_stat):
    ok_repos_number = 0
    for repo_stat in repos_stat:
        print(repo_stat['repo_name'])  # noqa: T001
        for error_slug, error_texts in sorted(repo_stat['errors'].items()):
            error_color = SEVERITY_COLORS[ERRORS_SEVERITY[error_slug]]
            for error_text in error_texts:
                print(f'\t{error_color}{error_slug}: {error_text}{attr(0)}')  # noqa: T001
        if not repo_stat['errors']:
            ok_repos_number += 1
            print(f'\t{fg(2)}ok{attr(0)}')  # noqa: T001
    ok_repos_percent = ok_repos_number / len(repos_stat) * 100
    print(  # noqa: T001
        f'{ok_repos_percent:.2f}% of all repos are ok ({ok_repos_number} of {len(repos_stat)})',
    )


def prepare_html_report(
    owner: str,
    repos_stat: List[RepoResult],
    html_template_path: str,
    extra_context_provider_py_name: str,
    result_filename: str,
    config,
) -> None:
    context = {
        'owner': owner,
        'repos': sorted(repos_stat, key=lambda r: len(r.errors)),
        'severity_colors': {'ok': 'green', 'warning': 'yellow', 'critical': 'red'},
        'downloads_last_week_stat': fetch_downloads_stat(repos_stat),
        **get_total_stat(repos_stat),
    }
    render_html_report(context, html_template_path, result_filename)


def get_total_stat(repos_stat):
    return {
        'checked_repos_number': len(repos_stat),
        'ok_repos_number': sum(1 for r in repos_stat if r.status == 'ok'),
        'repos_with_warnings_number': sum(1 for r in repos_stat if r.status == 'warning'),
        'critical_repos_number': sum(1 for r in repos_stat if r.status == 'critical'),
    }


def render_html_report(
    context: Mapping[str, Any],
    template_file_name: str,
    result_file: str,
) -> None:
    with open(template_file_name, 'r') as file_handler:
        template = file_handler.read()
    rendered_template = Template(template).render(**context)
    with open(result_file, 'w') as file_handler:
        file_handler.write(rendered_template)