from typing import List


def if_logs_has_any_of_commands(log: List[str], commands: List[str]) -> bool:
    is_section_present = False
    for required_command in commands:
        for base_command in log:
            if (
                base_command.startswith(f'{required_command} ')
                or f' {required_command} ' in base_command
                or base_command == required_command
            ):
                is_section_present = True
                break
    return is_section_present
