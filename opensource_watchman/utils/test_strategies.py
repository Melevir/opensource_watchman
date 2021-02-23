from hypothesis.strategies import from_type, composite, one_of, text, sampled_from
from typing import Callable

from opensource_watchman.common_types import GithubPipelineData


@composite
def github_data_with_yaml_config(draw: Callable) -> GithubPipelineData:
    yaml_content = one_of(
        sampled_from([
            'foo:\n  - bar  - baz',
            'foo: 1\nbar: 2',
            '',
        ]),
        text(),
    )
    item = draw(from_type(GithubPipelineData))
    item['ci_config_content'] = draw(yaml_content)
    item['ow_repo_config'] = draw(sampled_from([
        {},
        {'main_languages': 'python'},
    ]))
    return item
