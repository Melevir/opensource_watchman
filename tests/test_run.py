from opensource_watchman.composer import AdvancedComposer
from opensource_watchman.run import run_watchman


def test_run_calls_pipelines(owner, repo_name, ow_config, pipeline_result, mocker):
    mock = mocker.patch.object(AdvancedComposer, 'run_all', return_value=pipeline_result)
    run_watchman(
        owner=owner,
        repo_name=repo_name,
        exclude_list=[],
        config=ow_config,
    )
    assert mock.call_count == 3
