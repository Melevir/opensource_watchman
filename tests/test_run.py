from opensource_watchman.api.github import GithubRepoAPI
from opensource_watchman.composer import AdvancedComposer
from opensource_watchman.run import run_watchman, get_repos_names


def test_run_calls_pipelines(owner, repo_name, ow_config, pipeline_result, mocker):
    mock = mocker.patch.object(AdvancedComposer, 'run_all', return_value=pipeline_result)
    run_watchman(
        owner=owner,
        repo_name=repo_name,
        exclude_list=[],
        config=ow_config,
    )
    assert mock.call_count == 3


def test_get_repos_names(mocker, owner, github_login, github_token):
    mocker.patch.object(
        GithubRepoAPI,
        'fetch_repos_list',
        return_value=[
            {'archived': True, 'updated_at': '2021-01-20T00:00:00Z', 'name': 'test2'},
            {'archived': False, 'updated_at': '2021-01-22T00:00:00Z', 'name': 'test'},
        ]
    )

    actual_result = get_repos_names(owner, github_login, github_token, skip_archived=True)
    assert actual_result == ['test']
