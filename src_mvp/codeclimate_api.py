import os
from typing import Optional, Any, Mapping

from requests import get


def get_repo_info(owner: str, repo_name: str) -> Optional[Mapping[str, Any]]:
    response = get(
        f'https://api.codeclimate.com/v1/repos?github_slug={owner}/{repo_name}',
        headers={'Authorization': f'Token token={os.environ.get("CODECLIMATE_API_TOKEN")}'},
    )
    if response:
        raw_data = response.json()['data']
        return raw_data[0] if raw_data else None


def get_repo_id(owner: str, repo_name: str) -> Optional[str]:
    repo_info = get_repo_info(owner, repo_name)
    return repo_info['id'] if repo_info else None


def get_badge_token(owner: str, repo_name: str) -> Optional[str]:
    repo_info = get_repo_info(owner, repo_name)
    return repo_info['attributes']['badge_token'] if repo_info else None


def get_test_coverage(repo_id: str) -> Optional[float]:
    response = get(f'https://api.codeclimate.com/v1/repos/{repo_id}/test_reports')
    coverage = None
    if response:
        raw_data = response.json()
        coverage = raw_data['data'][0]['attributes']['covered_percent'] if raw_data['data'] else None
    return coverage
