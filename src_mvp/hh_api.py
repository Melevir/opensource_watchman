from typing import Mapping, Any, List

from requests import get


def filter_vacancies(
    vacancies_list: List[Mapping[str, Any]],
    triggers: List[str],
) -> List[Mapping[str, Any]]:
    return [v for v in vacancies_list if any(t in v['name'].lower() for t in triggers)]


def get_actual_vacancies(hh_employer_id: int) -> List[Mapping[str, Any]]:
    response = get(f'https://api.hh.ru/vacancies?employer_id={hh_employer_id}&per_page=100')
    return response.json().get('items', []) if response else []
