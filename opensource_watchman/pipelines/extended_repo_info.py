from typing import List

from opensource_watchman.api.pypistats import get_pypi_downloads_stat
from opensource_watchman.common_types import RepoResult


def fetch_downloads_stat(repos_stats: List[RepoResult]):
    downloads_last_week_stat = {}
    for repo in repos_stats:
        pypi_stat = get_pypi_downloads_stat(repo.package_name) if repo.package_name else None
        downloads_last_week_stat[repo.repo_name] = pypi_stat.get('last_week') if pypi_stat else None
    return downloads_last_week_stat
