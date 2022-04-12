import time
import random
import config
# Set the random seed, if applicable
if config.RANDOM_SEED is not None:
    random.seed(config.RANDOM_SEED)


class Monitor:
    """A narrative style control monitor."""

    def __init__(self, lexical_expressions):
        """Initialize a Monitor object."""
        # This is a dictionary mapping nouns and relations to their lexical expressions
        self.lexical_expressions = lexical_expressions

    def __str__(self):
        """Return string representation."""
        return "Narrative Style Control Monitor"

    def __repr__(self):
        """Return string representation."""
        return self.__str__()

    def report(self, universe):
        """Generate a report on the history of the given universe."""
        filename = f"reports/report-{int(time.time())}-{config.RANDOM_SEED}.txt"
        report = open(filename, "w")
        all_time_frames_in_order = sorted(universe.history.keys())
        for i, time_frame in enumerate(all_time_frames_in_order):
            report.write(f"\n\n\t{time_frame}\n\n")
            if i == 0:
                actions_this_time_frame = universe.history[time_frame]
            else:
                actions_this_time_frame = set(universe.history[time_frame]) - set(universe.history[all_time_frames_in_order[i-1]])
            for action in sorted(actions_this_time_frame, key=lambda triple: triple.id):
                action_subject = random.choice(self.lexical_expressions[action.subject])
                try:
                    action_relation = random.choice(self.lexical_expressions[action.relation])
                except KeyError:
                    error_message = f"Missing lexical expression for relation {action.relation} "
                    error_message += f"in action {action}."
                    raise Exception(error_message)
                try:
                    action_object = random.choice(self.lexical_expressions[action.object])
                except KeyError:
                    action_object = None
                if action_object:
                    # Use two spaces after a period, as in Klein (1971)
                    sentence = f"{action_subject} {action_relation} {action_object}.  "
                else:
                    sentence = f"{action_subject} {action_relation}.  "
                report.write(sentence)
        report.close()
 