from typing import Optional, NamedTuple

from requests import get


class CodeClimateAPI(NamedTuple):
    owner: str
    repo_name: str
    api_token: str
    code_climate_repo_id: Optional[str]

    @staticmethod
    def create(owner, repo_name, api_token):
        return CodeClimateAPI(
            owner,
            repo_name,
            api_token,
            CodeClimateAPI(owner, repo_name, api_token, None).get_repo_id(),
        )

    def get_repo_info(self):
        response = get(
            f'https://api.codeclimate.com/v1/repos?github_slug={self.owner}/{self.repo_name}',
            headers={'Authorization': f'Token token={self.api_token}'},
        )
        if response:
            raw_data = response.json()['data']
            return raw_data[0] if raw_data else None

    def get_repo_id(self) -> Optional[str]:
        repo_info = self.get_repo_info()
        return repo_info['id'] if repo_info else None

    def get_badge_token(self) -> Optional[str]:
        repo_info = self.get_repo_info()
        return repo_info['attributes']['badge_token'] if repo_info else None

    def get_test_coverage(self) -> Optional[float]:
        response = get(
            f'https://api.codeclimate.com/v1/repos/{self.code_climate_repo_id}/test_reports',
        )
        coverage = None
        if response:
            raw_data = response.json()
            if raw_data['data']:
                coverage = raw_data['data'][0]['attributes']['covered_percent']
        return coverage
