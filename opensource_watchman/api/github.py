from typing import Optional, Any, Mapping, NamedTuple

from requests import get
from requests.auth import HTTPBasicAuth


class GithubRepoAPI(NamedTuple):
    owner: str
    repo_name: Optional[str]
    github_login: str
    github_api_token: str

    def _fetch_data_from_github(self, relative_url: str) -> Optional[Mapping[str, Any]]:
        raw_response = get(
            f'https://api.github.com{relative_url}',
            auth=HTTPBasicAuth(self.github_login, self.github_api_token),
        )
        return raw_response.json() if raw_response else None

    def _fetch_data_from_github_repo(self, relative_url: str) -> Optional[Mapping[str, Any]]:
        return self._fetch_data_from_github(
            relative_url=f'/repos/{self.owner}/{self.repo_name}{relative_url}',
        )

    def fetch_repos_list(self):
        return self._fetch_data_from_github(relative_url=f'/users/{self.owner}/repos')

    def fetch_file_contents(self, file_path: str) -> Optional[str]:
        file_url = (
            f'https://raw.githubusercontent.com/{self.owner}/{self.repo_name}/master/{file_path}'
        )
        response = get(file_url)
        return response.text if response else None

    def fetch_repo_info(self):
        return self._fetch_data_from_github_repo(relative_url='')

    def fetch_commits(self, pull_request_number: int = None):
        if pull_request_number:
            return self._fetch_data_from_github_repo(
                relative_url=f'/pulls/{pull_request_number}/commits',
            ) or []
        return self._fetch_data_from_github_repo(relative_url='/commits')

    def fetch_commit_status(self, commit_sha: str):
        return self._fetch_data_from_github_repo(relative_url=f'/commits/{commit_sha}/statuses')

    def fetch_commit_reviews(self, commit_sha: str):
        return self._fetch_data_from_github_repo(relative_url=f'/commits/{commit_sha}/reviews')

    def fetch_open_issues(self):
        return self._fetch_data_from_github_repo(relative_url='/issues') or []

    def fetch_issue_comments(self, issue_number: int):
        return self._fetch_data_from_github_repo(
            relative_url=f'/issues/{issue_number}/comments',
        ) or []

    def fetch_open_pull_requests(self):
        return self._fetch_data_from_github_repo(relative_url='/pulls') or []

    def fetch_pull_request(self, pr_number: int):
        return self._fetch_data_from_github_repo(relative_url=f'/pulls/{pr_number}')

    def fetch_pull_request_comments(self, pr_number: int):
        return self._fetch_data_from_github_repo(relative_url=f'/pulls/{pr_number}/comments')
