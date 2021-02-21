from fn_graph import Composer


class AdvancedComposer(Composer):
    def run_all(self):
        return self.calculate(self._functions.keys(), intermediates=True)
