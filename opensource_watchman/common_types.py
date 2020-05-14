from typing import NamedTuple, List, Mapping
import enum


class RepoStatus(enum.Enum):
    ok = 'ok'
    has_warnings = 'has_warnings'
    has_errors = 'has_errors'


class RepoResult(NamedTuple):
    owner: str
    name: str
    status: RepoStatus
    violations_ids: List[str]


class OpensourceWatchmanConfig(NamedTuple):
    config_file_name: str
    config_section_name: str
    readme_file_name: str
    ci_config_file_name: str
    package_name_path: str
    github_login: str
    github_api_token: str
    travis_api_login: str
    required_readme_sections: List[List[str]]
    required_commands_to_run_in_build: List[Mapping]
    required_python_versions: List[str]
    max_age_of_last_commit_in_months: int
    code_climate_api_token: str
    min_test_coverage_percents: int
    min_number_of_actual_issues: int
    max_issue_update_age_months: int
    max_ok_pr_age_days: int
