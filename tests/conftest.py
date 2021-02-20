import pytest
import responses

from opensource_watchman.common_types import RepoResult


@pytest.fixture
def ok_repo_result():
    return RepoResult(
        owner='owner',
        package_name='test',
        description='test description',
        badges_urls=[],
        repo_name='test_repo',
        errors={},
    )


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps
