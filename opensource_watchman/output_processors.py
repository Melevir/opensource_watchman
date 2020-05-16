import importlib
import os
from typing import Any, Mapping, List, Optional

from colored import fg, attr
from jinja2 import Environment, FileSystemLoader

from opensource_watchman.pipelines.extended_repo_info import fetch_downloads_stat
from opensource_watchman.common_types import RepoResult
from opensource_watchman.config import SEVERITY_COLORS, ERRORS_SEVERITY


def print_errors_data(repos_stat):
    ok_repos_number = 0
    for repo_stat in repos_stat:
        print(repo_stat.repo_name)  # noqa: T001
        for error_slug, error_texts in sorted(repo_stat.errors.items()):
            error_color = SEVERITY_COLORS[ERRORS_SEVERITY[error_slug]]
            for error_text in error_texts:
                print(f'\t{error_color}{error_slug}: {error_text}{attr(0)}')  # noqa: T001
        if not repo_stat.errors:
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
    extra_context_provider_py_name: Optional[str],
    result_filename: str,
    config,
) -> None:
    context = {
        'owner': owner,
        'repos': sorted(repos_stat, key=lambda r: len(r.errors)),
        'severity_colors': {'ok': 'green', 'warning': 'yellow', 'critical': 'red'},
        'downloads_last_week_stat': fetch_downloads_stat(repos_stat),
        **get_total_stat(repos_stat),
        **get_extra_context_from_provider(extra_context_provider_py_name),
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
    template_file_path: str,
    result_file: str,
) -> None:
    templates_pathes = [
        os.path.dirname(os.path.dirname(__file__)),
        os.path.join(os.path.dirname(__file__), 'templates'),
    ]
    template_name = template_file_path
    if template_file_path.startswith(os.path.sep):
        templates_pathes.insert(0, os.path.dirname(template_file_path))
        template_name = os.path.basename(template_file_path)
    elif os.path.sep in template_file_path:
        templates_pathes.insert(
            0,
            os.path.join(os.path.abspath(os.getcwd()), os.path.dirname(template_file_path)),
        )
        template_name = os.path.basename(template_file_path)

    env = Environment(
        loader=FileSystemLoader(templates_pathes),
    )
    template = env.get_template(template_name)
    rendered_template = template.render(**context)

    with open(result_file, 'w') as file_handler:
        file_handler.write(rendered_template)


def get_extra_context_from_provider(extra_context_provider_py_name: Optional[str]):
    if not extra_context_provider_py_name:
        return {}
    module_to_import = '.'.join(extra_context_provider_py_name.split('.')[:-1])
    module = importlib.import_module(module_to_import)
    callable_name = extra_context_provider_py_name.split('.')[-1]
    result = getattr(module, callable_name)()
    return result or {}
