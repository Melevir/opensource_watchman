from typing import Any, Mapping

from fn_graph import Composer


class AdvancedComposer(Composer):
    def run_all(self) -> Mapping[str, Any]:
        return self.calculate(self._functions.keys(), intermediates=True)
