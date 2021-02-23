from inspect import signature

from deal import cases as deal_cases, cached_property
from hypothesis.strategies import (
    from_type, composite, one_of, text, sampled_from,
    SearchStrategy, lists, datetimes,
)
from typing import Callable

from opensource_watchman.common_types import GithubPipelineData, GithubIssue, TravisPipelineData


@composite
def github_issue(draw: Callable) -> GithubIssue:
    item = draw(from_type(GithubIssue))
    item['updated_at'] = draw(datetimes().map(lambda d: d.isoformat(timespec='seconds') + 'Z'))
    item['comments'] = draw(lists(text(), min_size=1))
    return item


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
    item['open_issues'] = draw(lists(github_issue()))
    item['ow_repo_config'] = draw(sampled_from([
        {},
        {'main_languages': 'python'},
    ]))
    item['issues_comments'] = {i['number']: [i] for i in item['open_issues']}
    return item


@composite
def travis_build_strategy(draw: Callable) -> TravisPipelineData:
    item = draw(from_type(TravisPipelineData))
    item['last_build_commands'] = draw(lists(text(), min_size=1))
    return item


class cases(deal_cases):  # noqa: N801
    default_count = 50
    types_to_strategy_map = {
        GithubPipelineData: github_data_with_yaml_config(),
        TravisPipelineData: travis_build_strategy(),
    }

    def __init__(self, *args, **kwargs) -> None:
        if 'count' not in kwargs:
            kwargs['count'] = self.default_count
        super().__init__(*args, **kwargs)

    @cached_property
    def strategy(self) -> SearchStrategy:
        kwargs = self.kwargs.copy()
        for parameter_name, parameter in signature(self.func).parameters.items():
            param_type = parameter.annotation
            if param_type in self.types_to_strategy_map:
                kwargs[parameter_name] = self.types_to_strategy_map[param_type]
        self.kwargs = kwargs
        return super().strategy
