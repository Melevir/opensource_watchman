import deal

from opensource_watchman.api.codeclimate_api import CodeClimateAPI
from opensource_watchman.api.travis import TravisRepoAPI


test_travis_extract_commands_from_raw_log = deal.cases(TravisRepoAPI._extract_commands_from_raw_log)
