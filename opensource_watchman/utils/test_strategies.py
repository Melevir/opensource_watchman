from inspect import signature

from deal import cases as deal_cases, cached_property
from hypothesis.strategies import from_type, composite, one_of, text, sampled_from, SearchStrategy
from typing import Callable

from opensource_watchman.common_types import GithubPipelineData


@composite
def github_data_with_yaml_config(draw: Callable) -> GithubPipelineData:
    yaml_content = one_of(
        sampled_from([
            'foo:\n  - bar  - baz',
            'foo: 1\nbar: 2',
            'foo\nbar: 2',  # invalid yaml
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


class cases(deal_cases):
    types_to_strategy_map = {
        GithubPipelineData: github_data_with_yaml_config()
    }

    @cached_property
    def strategy(self) -> SearchStrategy:
        kwargs = self.kwargs.copy()
        for parameter_name, parameter in signature(self.func).parameters.items():
            param_type = parameter.annotation
            if param_type in self.types_to_strategy_map:
                kwargs[parameter_name] = self.types_to_strategy_map[param_type]
        self.kwargs = kwargs
        return super().strategy
