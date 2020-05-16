# opensource_watchman

[![Build Status](https://travis-ci.org/Melevir/opensource_watchman.svg?branch=master)](https://travis-ci.org/Melevir/opensource_watchman)
[![Maintainability](https://api.codeclimate.com/v1/badges/56b0ffab734dad488a41/maintainability)](https://codeclimate.com/github/Melevir/opensource_watchman/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/56b0ffab734dad488a41/test_coverage)](https://codeclimate.com/github/Melevir/opensource_watchman/test_coverage)

Opensource Github repos validator.

This tool checks project compliance with
[BestDoctor opensource guide](https://github.com/best-doctor/guides/blob/master/guides/opensource_guide.md).
It check project data from Github, TravisCI, CodeClimate and PyPIstats and
checks if project matches all rules from the guide. The tool outputs data
to console and can generate html report
(like <https://opensource.bestdoctor.ru/>). See "Errors" section of this
readme to see full list of possible errors.

## Installation

```terminal
pip install opensource_watchman
```

## Usage

Check all repos in Github organization/user:

```terminal
opensource_watchman {github username or organisation}
```

Check single repo:

```terminal
opensource_watchman {github username or organisation} --repo_name={repo_name}
```

Rest of watchman parameters can be viewed with `opensource_watchman --help`.

To run watchman, some environment variables must be provided:

- `GITHUB_USERNAME`. This is login to use api, not login to check.
- `GITHUB_API_TOKEN`. This should be create with account above.
  [Instructions on how to get one.](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line)
- `TRAVIS_CI_ORG_ACCESS_TOKEN`.
  [Can be generated from Github token.](https://docs.travis-ci.com/api/#with-a-github-token)
- `CODECLIMATE_API_TOKEN`. Can be requested in
  [tokens page in profile.](https://codeclimate.com/profile/tokens)

## Example

```terminal
$ opensource_watchman/run.py Melevir --repo_name=opensource_watchman
opensource_watchman
    D02: None of following found in readme: installation
    D02: None of following found in readme: contributing,contribution
    D02: None of following found in readme: usage,example
    R02: Package opensource_watchman is not released at PyPI
    T03: Test coverage is too low (1.57<80)
```

## Errors

| code |                     Description                                    |
|:----:|:------------------------------------------------------------------:|
| D01  | {readme file name} not found                                       |
| D02  | None of following found in readme: {missing readme sections}       |
| C01  | {ci_config_file_name} not found                                    |
| C02  | Current build status on Travis is not ok                           |
| C03  | {required build command} found in build                            |
| C04  | Travis badge not found in {readme_file_name}                       |
| C05  | Travis weekly cron build is not enabled                            |
| P01  | Travis build is not running on Python {required_python_version}    |
| R01  | Package name not found at {package_name_path}                      |
| R02  | Package {package_name} is not released at PyPI                     |
| S01  | Last commit was at {last_commit_date}, more that 6 months ago      |
| T01  | {owner}/{repo_name} not found at Codeclimate                       |
| T02  | No test coverage info found for {owner}/{repo_name} at Codeclimate |
| T03  | Test coverage is too low                                           |
| T04  | Codeclimate test coverage badge not found at {readme_file_name}    |
| I01  | Too few actual issues                                              |
| M01  | Pull request #{pr_number} is stale for too long                    |

## Contributing

We would love you to contribute to our project. It's simple:

- Create an issue with bug you found or proposal you have.
  Wait for approve from maintainer.
- Create a pull request. Make sure all checks are green.
- Fix review comments if any.
- Be awesome.

Here are useful tips:

- You can run all checks and tests with `make check`. Please do it
  before TravisCI does.
- We use
  [BestDoctor python styleguide](https://github.com/best-doctor/guides/blob/master/guides/en/python_styleguide.md).
- We respect [Django CoC](https://www.djangoproject.com/conduct/).
  Make soft, not bullshit.
