from colored import fg


ERRORS_SEVERITY = {
    'D01': 'critical',
    'D02': 'warning',
    'C01': 'critical',
    'C02': 'critical',
    'C03': 'warning',
    'C04': 'warning',
    'C05': 'critical',
    'P01': 'warning',
    'R01': 'warning',
    'R02': 'critical',
    'S01': 'critical',
    'T01': 'critical',
    'T02': 'critical',
    'T03': 'warning',
    'T04': 'warning',
    'I01': 'warning',
    'M01': 'critical',
}
SEVERITY_COLORS = {
    'warning': fg(3),
    'critical': fg(1),
}

DEFAULT_HTML_REPORT_FILE_NAME = 'report.html'
