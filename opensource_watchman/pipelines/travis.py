from super_mario import BasePipeline, input_pipe, process_pipe

from opensource_watchman.api.travis import TravisRepoAPI


class TravisReceiveDataPipeline(BasePipeline):
    pipeline = [
        'create_api',
        'fetch_last_build',
        'create_badge_url',
        'fetch_crontabs_info',
    ]

    @process_pipe
    @staticmethod
    def create_api(owner: str, repo_name: str, travis_api_login: str):
        return {'api': TravisRepoAPI(owner, repo_name, travis_api_login)}

    @input_pipe
    @staticmethod
    def fetch_last_build(api):
        return {
            'last_build': api.fetch_last_build_info(),
            'last_build_commands': api.get_last_build_commands(),
        }

    @process_pipe
    @staticmethod
    def create_badge_url(owner: str, repo_name: str):
        return {'badge_url': f'https://travis-ci.org/{owner}/{repo_name}.svg'}

    @input_pipe
    @staticmethod
    def fetch_crontabs_info(api):
        return {'crontabs_info': api.fetch_crontabs_info()}
