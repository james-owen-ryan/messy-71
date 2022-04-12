import config
from compiler import Compiler
from universe import Universe
from monitor import Monitor


class MESSY:
    """A class modeled after Sheldon Klein's 1971 version of MESSY."""

    def __init__(self):
        """Initialize a MESSY object."""
        self.rules = Compiler.parse_rules_file(path_to_rules_file=config.PATH_TO_RULES_FILE)
        self.universe = Universe()
        self.monitor = Monitor(
            lexical_expressions=Compiler.parse_lexical_expressions_file(
                path_to_lexical_expressions_file=config.PATH_TO_LEXICAL_EXPRESSIONS_FILE
            )
        )
        self.validate()

    def __str__(self):
        """Return string representation."""
        return "Meta-Symbolic Simulation System"

    def __repr__(self):
        """Return string representation."""
        return "MESSY"

    def validate(self):
        """Validate the procedural content loaded for this run."""
        # Confirm that every noun and relation has a lexical expression
        for rule in self.rules:
            for action in rule.action_list:
                if not hasattr(action.subject, "class_name"):
                    if action.subject not in self.monitor.lexical_expressions:
                        error_message = f"No lexical expression for noun {action.subject} referenced in action {action}"
                        raise Exception(error_message)
                if action.relation.name not in self.monitor.lexical_expressions:
                    error_message = f"No lexical expression for relation {action.relation.name} referenced in action {action}"
                    raise Exception(error_message)
                if not hasattr(action.object, "class_name"):
                    if action.object and action.object not in self.monitor.lexical_expressions:
                        error_message = f"No lexical expression for noun {action.object} referenced in action {action}"
                        raise Exception(error_message)

    def simulate(self):
        """Simulate the next time frame in the given universe."""
        self.universe.history[self.universe.time] = list(self.universe.network)
        self._advance_time()
        self.universe.update()
        for rule in self.rules:
            rule.test(universe=self.universe)

    def terminate(self):
        """Wrap up simulation."""
        self.universe.history[self.universe.time] = list(self.universe.network)
        self._advance_time()
        self.universe.update()

    def _advance_time(self):
        """Advance the time frame of the simulated universe."""
        self.universe.time_since_start += config.TIMESTEP
        self.universe.time += config.TIMESTEP
        # Update the integer 24-hour clock
        time_str = str(self.universe.time)
        if len(time_str) == 3:
            time_str = '0' + time_str
        if time_str[-2:] == '60':
            time_str = str(int(time_str[:2])+1) + '00'
            if time_str == '2500':
                time_str = '2400'
        self.universe.time = int(time_str)

    def report(self):
        """Write to file a report on the history of the simulated universe."""
        self.monitor.report(universe=self.universe)
