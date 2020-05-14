from typing import Mapping, Any

from jinja2 import Template


def render_html_report(context: Mapping[str, Any], template_file_name: str, result_file: str) -> None:
    with open(template_file_name, 'r') as file_handler:
        template = file_handler.read()
    rendered_template = Template(template).render(context=context)
    with open(result_file, 'w') as file_handler:
        file_handler.write(rendered_template)
