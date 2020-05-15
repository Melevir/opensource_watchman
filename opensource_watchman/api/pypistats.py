from typing import Mapping, Optional

from requests import get


def get_pypi_downloads_stat(pypi_project_name: str) -> Optional[Mapping[str, int]]:
    response = get(f'https://pypistats.org/api/packages/{pypi_project_name}/recent')
    return response.json().get('data', []) if response else None
