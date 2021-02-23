from opensource_watchman.output_processors import print_errors_data


def test_print_errors_data_without_errors(repos_stat_without_errors, capsys):
    print_errors_data([repos_stat_without_errors])
    captured = capsys.readouterr()
    assert captured.out == (
        'test\n\t\x1b[38;5;2mok\x1b[0m\n100.00% of all repos are ok (1 of 1)\n'
    )


def test_print_errors_data_with_errors(repos_stat_with_errors, capsys):
    print_errors_data([repos_stat_with_errors])
    captured = capsys.readouterr()
    assert captured.out == (
        'test\n\t\x1b[38;5;3mD02: error\x1b[0m\n0.00% of all repos are ok (0 of 1)\n'
    )
