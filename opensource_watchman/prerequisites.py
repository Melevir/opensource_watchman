from typing import Mapping

import deal


@deal.pure
def python_only(repo_config: Mapping[str, str]) -> bool:
    return 'python' in repo_config.get('main_languages', '')


@deal.pure
def rus_only(repo_config: Mapping[str, str]) -> bool:
    return repo_config.get('language') == 'ru'
