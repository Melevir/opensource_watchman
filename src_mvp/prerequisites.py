from typing import Mapping, Any


def python_only(repo_config: Mapping[str, Any]) -> bool:
    return 'python' in repo_config.get('main_languages', '')


def rus_only(repo_config: Mapping[str, Any]) -> bool:
    return repo_config.get('language') == 'ru'
