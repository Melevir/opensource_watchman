from opensource_watchman.utils.logs_analiser import if_logs_has_any_of_commands


def test_if_logs_has_any_of_commands_success_case():
    assert if_logs_has_any_of_commands(['foo'], ['foo'])
    assert if_logs_has_any_of_commands(['foo'], ['foo', 'bar'])
    assert if_logs_has_any_of_commands(['bar'], ['foo', 'bar'])
    assert not if_logs_has_any_of_commands(['foo'], ['bar'])
