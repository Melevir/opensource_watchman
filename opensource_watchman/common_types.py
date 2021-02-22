import datetime
from typing import NamedTuple, List, Mapping, Dict, Optional, TypedDict, Callable  # noqa: TYP001
import enum

from opensource_watchman.config import ERRORS_SEVERITY


class RepoStatus(enum.Enum):
    ok = 'ok'
    has_warnings = 'has_warnings'
    has_errors = 'has_errors'


class RepoResult(NamedTuple):
    owner: str
    package_name: Optional[str]
    description: Optional[str]
    badges_urls: List[str]
    repo_name: str
    errors: Dict[str, List[str]]

    @property
    def status(self):
        if not self.errors:
            return 'ok'
        severities = {ERRORS_SEVERITY[e] for e in self. errors.keys()}
        return 'critical' if 'critical' in severities else 'warning'

    @property
    def iterate_errors_with_severities(self):
        for error_slug, errors in self.errors.items():
            for error in errors:
                yield error_slug, error, ERRORS_SEVERITY[error_slug]


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


class GithubIssue(TypedDict):
    updated_at: str
    comments: List[str]
    number: int


class GithubComment(TypedDict):
    updated_at: str


class GithubPullRequest(TypedDict):
    number: int
    updated_at: str


class GithubPullRequestStatus(TypedDict):
    state: str


class GithubPullRequestReview(TypedDict):
    state: str


class GithubPullRequestDetails(TypedDict):
    statuses_info: List[GithubPullRequestStatus]
    last_review: GithubPullRequestReview
    comments: List[GithubComment]
    number: int


class GithubPipelineData(TypedDict):
    ow_repo_config: Mapping[str, str]
    readme_file_name: str
    readme_content: str
    ci_config_file_name: str
    ci_config_content: str
    file_with_package_name_content: str
    last_commit_date: datetime.datetime
    open_issues: List[GithubIssue]
    issues_comments: Mapping[int, List[GithubComment]]
    open_pull_requests: List[GithubPullRequest]
    pull_request_details: Mapping[int, GithubPullRequestDetails]
    detailed_pull_requests: Mapping[int, GithubPullRequestDetails]


class TravisBuildState(TypedDict):
    state: str


class TravisCrontabInfo(TypedDict):
    interval: str


class TravisPipelineData(TypedDict):
    last_build: TravisBuildState
    last_build_commands: List[str]
    crontabs_info: List[TravisCrontabInfo]
    badge_url: str


class RequiredCICommandsConfig(TypedDict):
    prerequisites: List[Callable[[Mapping[str, str]], bool]]
    cmd: List[str]
