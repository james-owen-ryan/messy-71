import config
import random
import itertools
from utils import red, green, blue, yellow
if config.OUTPUT_TO_FILE:
    import sys
    sys.stdout = open(config.LOG_FILE, 'a')
# Set the random seed, if applicable
if config.RANDOM_SEED is not None:
    random.seed(config.RANDOM_SEED)


class Rule:
    """A simulation rule defined using Klein's (1971) rule language."""

    def __init__(self, action_list, subrules, raw_definition):
        """Initialize a Rule object."""
        self.action_list = action_list
        self.subrules = subrules
        self.raw_definition = raw_definition

    def __str__(self):
        """Return string representation."""
        return self.raw_definition

    def __repr__(self):
        """Return string representation."""
        return ", ".join(str(action) for action in self.action_list)

    def test(self, universe):
        """Test this rule, given the current state of the given universe."""
        if config.VERBOSITY >= 2:
            print(f"Testing rule: {self.action_list[0]}...")
        # Collect candidate bindings for action subjects and objects
        binding_candidates = {}
        y_restriction = float("inf")
        for action in self.action_list:
            # Collect candidate subjects
            if isinstance(action.subject, Variable):
                class_name = action.subject.class_name
                binding_candidates[action.subject.name] = universe.classes[class_name]
                if action.subject.y_restriction_part:
                    y_restriction = min(y_restriction, action.subject.y_restriction_part)
            else:
                binding_candidates[action.subject] = [action.subject]  # Ex: candidate_bindings['GEORGE'] = ['GEORGE']
            if action.object:
                # Collect candidate objects
                if isinstance(action.object, Variable):
                    class_name = action.object.class_name
                    binding_candidates[action.object.name] = universe.classes[class_name]
                    if action.object.y_restriction_part:
                        y_restriction = min(y_restriction, action.object.y_restriction_part)
                else:
                    binding_candidates[action.object] = [action.object]
        # Test all bindings, unless we reach a maximum specified by a Y-restriction part
        rule_executions = 0
        variable_ordering = list(binding_candidates.keys())
        candidate_bindings = list(itertools.product(*binding_candidates.values()))
        for ordered_candidates_list in candidate_bindings:
            if not config.ALLOW_DUPLICATE_ENTITIES_IN_VARIABLE_BINDINGS:
                if len(set(ordered_candidates_list)) != len(ordered_candidates_list):
                    continue
            candidate_binding = {}
            for i, variable_name in enumerate(variable_ordering):
                candidate_binding[variable_name] = ordered_candidates_list[i]
            if self._triggered(universe=universe, partial_bindings=candidate_binding):
                self.fire(universe=universe, bindings=candidate_binding)
                rule_executions += 1
                if rule_executions == y_restriction:
                    return

    def _triggered(self, universe, partial_bindings):
        """Return whether this rule fires with the given variable binding."""
        if config.VERBOSITY >= 3:
            print(f"  Bindings: {partial_bindings}")
        probability = 0.0
        if config.VERBOSITY >= 3:
            print(f"    Probability is {probability}")
        for subrule in self.subrules:
            if subrule.holds(universe=universe, partial_bindings=partial_bindings):
                increment = subrule.true_value
            else:
                increment = subrule.false_value
            # Potentially short-circuit
            if abs(increment) >= config.SHORT_CIRCUIT_PROBABILITY_INCREMENT_ABSOLUTE_THRESHOLD:
                if increment > 0:
                    if config.VERBOSITY >= 3:
                        print("    Short-circuit trigger!")
                    return True
                if config.VERBOSITY >= 3:
                    print("    Short-circuit abandon!")
                return False
            # Otherwise, increment the running probability
            probability += increment
            if config.VERBOSITY >= 3:
                print(f"    Probability is now {probability}")
        if random.random() < probability:
            if config.VERBOSITY >= 3:
                print(green(f"    Triggered!"))
            return True
        if config.VERBOSITY >= 3:
            print(f"    Did not trigger")
        return False

    def fire(self, universe, bindings):
        """Execute all the actions in the action list for this rule."""
        triples_to_add_next_time_frame = []
        for action in self.action_list:
            triple = action.execute(bindings=bindings)
            triples_to_add_next_time_frame.append(triple)
        universe.queue_triples(triples=triples_to_add_next_time_frame)


class Action:
    """An action to be executed upon a rule firing in Klein's (1971) simulation engine."""

    def __init__(self, action_subject, action_relation, action_object, raw_definition):
        """Initialize an Action object."""
        self.subject = action_subject
        self.relation = action_relation
        self.object = action_object  # None if this modifies an attribute
        self.raw_definition = raw_definition

    def __str__(self):
        """Return string representation."""
        return self.raw_definition

    def __repr__(self):
        """Return string representation."""
        return self.__str__()

    def execute(self, bindings):
        """Return a triple to be added to the network next time frame."""
        if isinstance(self.subject, Variable):
            ground_subject = bindings[self.subject.name]
        else:
            ground_subject = bindings[self.subject]
        if self.object is None:
            ground_object = None
        elif isinstance(self.object, Variable):
            ground_object = bindings[self.object.name]
        else:
            ground_object = bindings[self.object]
        triple_to_add = (ground_subject, self.relation, ground_object)
        if config.VERBOSITY >= 2:
            if ground_object:
                print(green(f"  {ground_subject} {self.relation} {ground_object}"))
            else:
                print(green(f"  {ground_subject} {self.relation}"))
        return triple_to_add


class Subrule:
    """A subrule in a rule defined using Klein's (1971) rule language."""

    def __init__(self, true_value, false_value, sentence_list, raw_definition):
        """Initialize a Subrule object."""
        self.true_value = true_value
        self.false_value = false_value
        self.sentence_list = sentence_list
        self.raw_definition = raw_definition

    def __str__(self):
        """Return string representation."""
        return self.raw_definition

    def __repr__(self):
        """Return string representation."""
        return self.__str__()

    def holds(self, universe, partial_bindings):
        """Return whether the condition expressed in this subrule holds, given the variable binding.

        Note that variables (besides any X or Y introduced in the rule header) cannot be passed
        across subrule boundaries, meaning the bindings are local to the subrule at hand (1971:13).
        """
        if config.VERBOSITY >= 3:
            print(f"  Testing subrule: {self.__str__()}")
        partial_bindings = {variable: [ground] for variable, ground in partial_bindings.items()}
        # Collect candidate bindings for all variables referenced in the sentence list
        flattened_sentence_list = []
        for item in self.sentence_list:
            if type(item) is list:
                flattened_sentence_list += item
            else:
                flattened_sentence_list.append(item)
        new_binding_candidates = {}
        for sentence in flattened_sentence_list:
            if not isinstance(sentence, Sentence):
                continue
            if isinstance(sentence.subject, Variable):
                if sentence.subject.name in partial_bindings:
                    continue
                class_name = sentence.subject.class_name
                new_binding_candidates[sentence.subject.name] = universe.classes[class_name]
            else:
                if sentence.subject in partial_bindings:
                    continue
                # Ex: candidate_bindings['GEORGE'] = ['GEORGE']
                new_binding_candidates[sentence.subject] = [sentence.subject]
        for sentence in flattened_sentence_list:
            if not isinstance(sentence, Sentence):
                continue
            if not sentence.object:
                continue
            if isinstance(sentence.object, Variable):
                if sentence.object.name in partial_bindings:
                    continue
                class_name = sentence.object.class_name
                new_binding_candidates[sentence.object.name] = universe.classes[class_name]
            else:
                if sentence.object in partial_bindings:
                    continue
                # Ex: candidate_bindings['GEORGE'] = ['GEORGE']
                new_binding_candidates[sentence.object] = [sentence.object]
        # Test all bindings
        binding_candidates = {**partial_bindings, **new_binding_candidates}  # Merge the two dictionaries
        variable_ordering = list(binding_candidates.keys())
        candidate_bindings = list(itertools.product(*binding_candidates.values()))
        for ordered_candidates_list in candidate_bindings:
            candidate_binding = {}
            for i, variable_name in enumerate(variable_ordering):
                candidate_binding[variable_name] = ordered_candidates_list[i]
            if config.VERBOSITY >= 3:
                print(f"    Binding: {candidate_binding}")
            this_rule_holds = self._evaluate_sentences(
                universe=universe,
                binding=candidate_binding,
                sentence_list=self.sentence_list
            )
            if this_rule_holds:
                return True
        return False

    def _evaluate_sentences(self, universe, binding, sentence_list):
        """Evaluate the given sentence(s) or list of sentence(s)."""
        sentence_list = list(sentence_list)  # Make a copy, to be safe
        while any(component for component in sentence_list if not isinstance(component, str)):
            for i, component in enumerate(sentence_list):
                if isinstance(component, list):
                    sentence_list[i] = self._evaluate_sentences(
                        universe=universe,
                        binding=binding,
                        sentence_list=component
                    )
                    continue
                if component == '&':
                    sentence_list[i] = 'and'
                    continue
                if component == '/':
                    sentence_list[i] = 'or'
                    continue
                if isinstance(component, str):
                    continue
                if isinstance(component, bool):
                    sentence_list[i] = str(component)
                    continue
                # If we get to here, it's a Sentence or a TimeSentence object
                if isinstance(component, Sentence):
                    sentence_list[i] = str(component.evaluate(bindings=binding, universe=universe))
                else:
                    sentence_list[i] = str(component.evaluate(universe=universe))
        return eval(' '.join(str(component) for component in sentence_list))


class Sentence:
    """A precondition ("sentence") on a subrule."""

    def __init__(self, sentence_subject, sentence_relation, sentence_object):
        """Initialize a Sentence object."""
        self.subject = sentence_subject
        self.relation = sentence_relation
        self.object = sentence_object

    def __str__(self):
        """Return string representation."""
        return f"{self.subject} {self.relation} {self.object}"

    def __repr__(self):
        """Return string representation."""
        return self.__str__()

    def evaluate(self, bindings, universe):
        """Return whether this sentence holds, given the binding and the current state of the modelled universe."""
        if isinstance(self.subject, Variable):
            ground_subject = bindings[self.subject.name]
        else:
            ground_subject = bindings[self.subject]
        if self.object is None:
            ground_object = None
        elif isinstance(self.object, Variable):
            ground_object = bindings[self.object.name]
        else:
            ground_object = bindings[self.object]
        evaluation = universe.match(
            triple_subject=ground_subject,
            triple_relation=self.relation,
            triple_object=ground_object
        )
        if config.VERBOSITY >= 3:
            print(f"      Evaluated sentence to {evaluation}: ({ground_subject} {self.relation} {ground_object})")
        return evaluation


class TimeSentence:
    """A precondition ("sentence") on a subrule pertaining to the current plot time."""

    def __init__(self, operator, time_value):
        """Initialize a TimeSentence object."""
        self.operator = operator
        self.time_value = int(time_value)

    def __str__(self):
        """Return string representation."""
        return f"T {self.operator} {self.time_value}"

    def __repr__(self):
        """Return string representation."""
        return self.__str__()

    def evaluate(self, universe):
        """Return whether this sentence holds, given the current time frame of the modelled universe."""
        if self.operator == '==':
            return universe.time == self.time_value
        if self.operator == '!=':
            return universe.time != self.time_value
        if self.operator == '<':
            return universe.time < self.time_value
        if self.operator == '>':
            return universe.time > self.time_value


class Relation:
    """A relation between nodes in a semantic network."""

    def __init__(self, name, negate_field, duration_modifier_operator, duration_modifier_time_value):
        """Initialize a Relation object."""
        self.name = name  # Name of the relation
        self.negate_field = negate_field  # True if this relation has a delete field or negate field
        if duration_modifier_operator:
            assert duration_modifier_time_value, (
                f"Relation '{name}' has duration_modifier_operator but no duration_modifier_time_value."
            )
        self.duration_modifier_operator = duration_modifier_operator
        self.duration_modifier_time_value = int(duration_modifier_time_value) if duration_modifier_time_value else None

    def __str__(self):
        """Return string representation."""
        negation = "!=" if self.negate_field else ''
        if self.duration_modifier_operator:
            duration_modifier = f"{self.duration_modifier_operator}{self.duration_modifier_time_value}"
        else:
            duration_modifier = ''
        return f"{negation}{self.name}{duration_modifier}"

    def __repr__(self):
        """Return string representation."""
        return self.__str__()


class Variable:
    """A variable in a rule."""

    def __init__(self, name, class_name=None, y_restriction_part=None):
        """Initialize a Variable object."""
        self.name = name
        self.class_name = class_name
        self.y_restriction_part = y_restriction_part

    def __str__(self):
        """Return string representation."""
        name = self.name if self.name else '#'
        class_name_component = f".{self.class_name}" if self.class_name else ''
        y_restriction_part_component = f":{self.y_restriction_part}" if self.y_restriction_part else ''
        return f"{name}{class_name_component}{y_restriction_part_component}"

    def __repr__(self):
        """Return string representation."""
        return self.__str__()
