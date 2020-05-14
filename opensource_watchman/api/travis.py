import re
from typing import Optional, Any, Mapping, NamedTuple, List

from requests import get


class TravisRepoAPI(NamedTuple):
    owner: str
    repo_name: str
    travis_api_token: str

    def _fetch_data_from_travis(
        self,
        relative_url: str,
        with_repo_prefix: bool = True,
    ) -> Optional[Mapping[str, Any]]:
        repo_prefix = f'/repo/{self.owner}%2F{self.repo_name}'
        raw_response = get(
            f'https://api.travis-ci.org{repo_prefix if with_repo_prefix else ""}{relative_url}',
            headers={
                'Authorization': f'token {self.travis_api_token}',
                'Travis-API-Version': '3',
            },
        )
        return raw_response.json() if raw_response else None

    def fetch_last_build_info(self):
        builds = self._fetch_data_from_travis(relative_url='/builds')
        return builds['builds'][0] if builds and builds.get('builds') else None

    def fetch_crontabs_info(self):
        crons = self._fetch_data_from_travis(relative_url='/crons')
        return crons['crons'] if crons else []

    def fetch_job_log(self, job_id):
        log = self._fetch_data_from_travis(
            relative_url=f'/job/{job_id}/log',
            with_repo_prefix=False,
        )
        return log['content'] if log else None

    def get_last_build_commands(self) -> List[str]:
        """
        Fetches last build log and get commands-like strings to guess
        what commands are included in build.
        """
        build_info = self.fetch_last_build_info()
        if not build_info:
            return []
        last_job_id = build_info['jobs'][0]['id']
        raw_log = self.fetch_job_log(last_job_id)
        if raw_log is None:
            return []
        return self._extract_commands_from_raw_log(raw_log)

    @staticmethod  # noqa: C901
    def _extract_commands_from_raw_log(raw_log):  # noqa: C901
        commands_with_subcommands = [
            # those commands have subcommands that are logged as stdout,
            # those commands should be extracted too
            'make',
        ]

        commands = [
            l.lstrip('\x1b[0K$ ')
            for l in raw_log.splitlines()
            if l.strip('\x1b[0K').startswith('$ ')
        ]
        lines = [l.lstrip('\x1b[0K$ ') for l in raw_log.splitlines()]

        for mother_command in commands_with_subcommands:
            start_section = None
            end_section = None
            for line_num, line in enumerate(lines):
                if line.startswith(f'{mother_command} ') and start_section is None:
                    start_section = line_num
                    continue
                if line.startswith('$ ') and start_section is not None and end_section is None:
                    end_section = line_num
                    break
            if end_section is None:
                end_section = len(lines) - 1
            if start_section and end_section:
                for line in lines[start_section:end_section]:
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
        return commands
