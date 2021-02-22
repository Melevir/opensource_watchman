import deal

from opensource_watchman.pipelines.github import (
    create_api, fetch_project_description, create_github_pipeline,
)
from opensource_watchman.pipelines.travis import create_travis_pipeline

test_github_create_api = deal.cases(create_api)
test_github_fetch_project_description = deal.cases(fetch_project_description)
test_create_github_pipeline = deal.cases(create_github_pipeline)
test_create_travis_pipeline = deal.cases(create_travis_pipeline)
