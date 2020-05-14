import os
import re
from typing import List, Any, Mapping, Optional

import requests


def get_last_build_info(owner: str, repo_name: str) -> Optional[Mapping[str, Any]]:
    build_response = requests.get(
        f'https://api.travis-ci.org/repo/{owner}%2F{repo_name}/builds',
        headers={
            'Authorization': f'token {os.environ.get("TRAVIS_CI_ORG_ACCESS_TOKEN")}',
            'Travis-API-Version': '3',
        }
    )
    raw_data = build_response.json() if build_response else None
    return raw_data['builds'][0] if raw_data and raw_data.get('builds') else None


def is_last_build_passed(owner: str, repo_name: str) -> bool:
    build_info = get_last_build_info(owner, repo_name)
    return build_info['state'] == 'passed' if build_info else False


def get_crontabs_info(owner: str, repo_name: str) -> List[Mapping[str, Any]]:
    crons_response = requests.get(
        f'https://api.travis-ci.org/repo/{owner}%2F{repo_name}/crons',
        headers={
            'Authorization': f'token {os.environ.get("TRAVIS_CI_ORG_ACCESS_TOKEN")}',
            'Travis-API-Version': '3',
        }
    )
    if not crons_response:
        return []
    return crons_response.json()['crons']


def get_last_build_commands(owner: str, repo_name: str) -> List[str]:
    """
    Fetches last build log and get commands-like strings to guess what commands are included in build.
    """
    commands_with_subcommands = [
        # those commands have subcommands that are logged as stdout,
        # those commands should be extracted too
        'make',
    ]
    build_info = get_last_build_info(owner, repo_name)
    if not build_info:
        return []
    last_job_id = build_info['jobs'][0]['id']
    raw_log = requests.get(
        f'https://api.travis-ci.org/job/{last_job_id}/log',
        headers={
            'Authorization': f'token {os.environ.get("TRAVIS_CI_ORG_ACCESS_TOKEN")}',
            'Travis-API-Version': '3',
        }
    ).json()['content']

    # executed_commads = [l.split('\n')[0] for l in raw_log.split('$ ')][1:]
    # return [e[5:] if e.startswith('sudo ') else e for e in executed_commads]

    commands = [l.lstrip('\x1b[0K$ ') for l in raw_log.splitlines() if l.strip('\x1b[0K').startswith('$ ')]

    lines = [l.lstrip('\x1b[0K$ ') for l in raw_log.splitlines()]
    # for l in lines:
    #     print(l)
    for mother_command in commands_with_subcommands:
        start_section = None
        end_section = None
        for line_num, line in enumerate(lines):
            # print('!!!!!!!', line)
            if line.startswith(f'{mother_command} ') and start_section is None:
                start_section = line_num
                continue
            if line.startswith('$ ') and start_section is not None and end_section is None:
                end_section = line_num
                break
        if end_section is None:
            end_section = len(lines) - 1
        # print('!!!', mother_command, start_section, end_section)
        if start_section and end_section:
            for line in lines[start_section:end_section]:
                # print('fff', line)
                if (
                    not line.strip()
                    or line.startswith('-')
                    or line.startswith('=')
                    or line.startswith('|')
                    or line.startswith('+')
                    or re.match(r'^make\[\d\]', line)
                    or line.startswith('Warning')
                    or line.startswith('Success')
                ):
                    continue
                commands.append(line)
    # print('???', commands)
    return commands
