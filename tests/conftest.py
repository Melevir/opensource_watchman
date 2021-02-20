import pytest
import responses

from opensource_watchman.api.codeclimate_api import CodeClimateAPI
from opensource_watchman.common_types import RepoResult


@pytest.fixture
def ok_repo_result(owner, repo_name):
    return RepoResult(
        owner=owner,
        package_name='test',
        description='test description',
        badges_urls=[],
        repo_name=repo_name,
        errors={},
    )


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def owner():
    return 'owner'


@pytest.fixture
def repo_name():
    return 'test_repo'


@pytest.fixture
def api_token():
    return '123-secret-api-token'


@pytest.fixture
def code_climate_api(mocked_responses, owner, repo_name, api_token):
    mocked_responses.add(
        responses.GET,
        f'https://api.codeclimate.com/v1/repos?github_slug={owner}/{repo_name}',
        json={'data': [{'id': 123}]},
    )
    return CodeClimateAPI.create(owner, repo_name, api_token)
