from typing import Any

import deal

from opensource_watchman.api.travis import TravisRepoAPI
from opensource_watchman.composer import AdvancedComposer


def create_api(owner: str, repo_name: str, travis_api_login: str):
    return TravisRepoAPI(owner, repo_name, travis_api_login)


def fetch_last_build(api):
    return api.fetch_last_build_info()


def fetch_last_build_commands(api):
    return api.get_last_build_commands()


def create_badge_url(owner: str, repo_name: str):
    return f'https://travis-ci.org/{owner}/{repo_name}.svg'


def fetch_crontabs_info(api):
    return api.fetch_crontabs_info()


@deal.pure
def create_travis_pipeline(**kwargs: Any) -> AdvancedComposer:
    return AdvancedComposer().update_parameters(**kwargs).update_without_prefix(
        'create_',
        create_api,
        create_badge_url,
    ).update_without_prefix(
        'fetch_',
        fetch_last_build,
        fetch_last_build_commands,
        fetch_crontabs_info,
    )
