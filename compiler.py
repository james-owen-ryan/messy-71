import re
import config
from rules import Rule, Action, Subrule, Sentence, Relation, TimeSentence, Variable


class Compiler:
    """A compiler for Klein's (1971) rule language."""

    @classmethod
    def parse_rules_file(cls, path_to_rules_file):
        """Parse the given rules file."""
        rule_objects = []
        # Read in the rules file
        lines = open(path_to_rules_file).readlines()
        # Convert to uppercase
        lines = [line.upper() for line in lines if line.strip()]
        # Remove blank lines
        lines = [line for line in lines if line.strip()]
        # Remove comments
        lines = [line for line in lines if not line.lstrip().startswith('%')]
        # Reduce all whitespace
        blob = ''.join(lines)
        blob = blob.replace('\n', ' ').replace('\t', ' ')
        while '  ' in blob:
            blob = blob.replace('  ', ' ')
        # Remove the asterisks (since to our current knowledge it does nothing)
        blob = blob.replace('*', '')
        # Replace '≠' symbols with '!=', for ease of parsing, etc. Klein's original
        # language appears to have used '≠'.
        blob = blob.replace('≠', '!=')
        # Replace '←' symbols with '<-', for ease of parsing, etc. Klein's original
        # language appears to have used '←'.
        blob = blob.replace('←', '<-')
        # Break into individual rule definitions
        rule_definitions = [line.strip() for line in blob.split('$RULE') if line]
        # Parse each rule definition
        for rule_definition in rule_definitions:
            rule_object = cls._parse_rule_definition(rule_definition=rule_definition)
            rule_objects.append(rule_object)
        return rule_objects

    @classmethod
    def _parse_rule_definition(cls, rule_definition):
        """Return a Rule object, given a raw rule definition."""
        action_list_definition, *subrule_definitions = [component.strip() for component in rule_definition.split(';')]
        # Parse action list
        action_definitions = [action_definition.strip() for action_definition in action_list_definition.split(',')]
        action_list = cls._parse_action_definitions(action_definitions=action_definitions)
        subrules = cls._parse_subrule_definitions(subrule_definitions=subrule_definitions)
        rule_object = Rule(action_list=action_list, subrules=subrules, raw_definition=rule_definition)
        return rule_object

    @classmethod
    def _parse_action_definitions(cls, action_definitions):
        """Parse the given action definitions."""
        action_list = []
        variables_in_this_scope = {}  # Updated by cls._parse_variable_or_noun()
        for action_definition in action_definitions:
            if not action_definition.strip():
                continue
            if config.VERBOSITY >= 2:
                print(f"Parsing action definition: {action_definition}")
            components = action_definition.split()
            if len(components) == 3:
                raw_subject, raw_relation, raw_object = components
            else:
                raw_subject, raw_relation = components
                raw_object = None
            action_subject, variables_in_this_scope = cls._parse_variable_or_noun(
                reference=raw_subject,
                variables_in_this_scope=variables_in_this_scope
            )
            try:
                if action_subject.name == 'X':
                    x = action_subject
                elif action_subject.name == 'Y':
                    y = action_subject
            except AttributeError:
                pass
            relation, left_directed = cls._parse_relation(reference=raw_relation)
            if raw_object:
                action_object, variables_in_this_scope = cls._parse_variable_or_noun(
                    reference=raw_object,
                    variables_in_this_scope=variables_in_this_scope
                )
            else:
                action_object = None
            if left_directed:
                action_subject, action_object = action_object, action_subject
            action = Action(
                action_subject=action_subject,
                action_relation=relation,
                action_object=action_object,
                raw_definition=action_definition
            )
            action_list.append(action)
        return action_list

    @classmethod
    def _parse_subrule_definitions(cls, subrule_definitions):
        """Parse the given subrule definitions."""
        subrules = []
        for subrule_definition in subrule_definitions:
            if not subrule_definition.strip():
                continue
            if config.VERBOSITY >= 2:
                print(f"Parsing subrule: {subrule_definition}")
            raw_probability_increments, raw_sentence_list = subrule_definition.split(':')
            # Parse the probability increments ("true value" and "false value")
            raw_true_value, raw_false_value = raw_probability_increments.split(',')
            true_value = float(raw_true_value)
            false_value = float(raw_false_value)
            # Parse the subrule conditions ("sentence list")
            variables_in_this_scope = {}
            sentence_list = []
            sentence_list_components = re.findall('\[[^\]]*\]|\([^\)]*\)|\"[^\"]*\"|\S+', raw_sentence_list)
            for component in sentence_list_components:
                if component.strip() in ('/', '&'):
                    sentence_list.append(component.strip())
                    continue
                new_sentence_sublist, variables_in_this_scope = cls._parse_sentence(
                    sentence_definition=component,
                    variables_in_this_scope=variables_in_this_scope
                )
                sentence_list.append(new_sentence_sublist)
            subrule_object = Subrule(
                true_value=true_value,
                false_value=false_value,
                sentence_list=sentence_list,
                raw_definition=subrule_definition
            )
            subrules.append(subrule_object)
        return subrules

    @staticmethod
    def _parse_variable_or_noun(reference, variables_in_this_scope):
        """Parse the given reference to return either a Variable object or string (noun, i.e., a literal)."""
        # Parse for X or Y, which are reserved names
        if reference in ('X', 'Y'):
            variable_name = reference
            if reference in variables_in_this_scope:
                existing_variable = variables_in_this_scope[variable_name]
                return existing_variable, variables_in_this_scope
            new_variable = Variable(name=variable_name)
            variables_in_this_scope[variable_name] = new_variable
            return new_variable, variables_in_this_scope
        if reference.startswith('X.'):  # This should only occur upon first definition
            variable_name, class_name = reference.split('.')
            new_variable = Variable(name=variable_name, class_name=class_name)
            variables_in_this_scope[variable_name] = new_variable
            return new_variable, variables_in_this_scope
        if reference.startswith('Y.'):  # This should only occur upon first definition
            if ':' in reference:
                variable_name, remainder = reference.split('.')
                # Only Y can have a "Y-restriction part" (p. 6, 16)
                class_name, y_restriction_part = remainder.split(':')
                y_restriction_part = int(y_restriction_part)
            else:
                variable_name, class_name = reference.split('.')
                y_restriction_part = None
            new_variable = Variable(name=variable_name, class_name=class_name, y_restriction_part=y_restriction_part)
            variables_in_this_scope[variable_name] = new_variable
            return new_variable, variables_in_this_scope
        # Parse for any other variable, marked by a leading '#'
        if reference.startswith('#'):
            reference = reference[1:]  # Strip off the leading '#'
            if '.' in reference:  # This should only occur upon first definition
                variable_name, class_name = reference.split('.')
                variable_name = None if not variable_name else variable_name  # E.g., "#.ROOMS"
                new_variable = Variable(name=variable_name, class_name=class_name)
                variables_in_this_scope[variable_name] = new_variable
                return new_variable, variables_in_this_scope
            if reference in variables_in_this_scope:
                existing_variable = variables_in_this_scope[reference]
                return existing_variable, variables_in_this_scope
            new_variable = Variable(name=reference)
            variables_in_this_scope[reference] = new_variable
            return new_variable, variables_in_this_scope
        # If we get to here, it's just a name (literal)
        return reference, variables_in_this_scope

    @staticmethod
    def _parse_relation(reference):
        """Parse a relation reference."""
        negate_field = False
        left_directed_relation = False
        # Check for delete field or negation field (e.g., "!=MAD")
        if reference.startswith('!='):
            negate_field = True
            reference = reference[2:]
        # Check for directed relation (e.g., "<-LIKES")
        if reference.startswith('<-'):
            left_directed_relation = True
            reference = reference[2:]
        # Check for duration modifier
        duration_modifier_time_value = None
        for duration_modifier_operator in ('!=', '=', '<', '>'):
            if duration_modifier_operator in reference:
                relation_name, duration_modifier_time_value = reference.split(duration_modifier_operator)
                break
        else:
            duration_modifier_operator = None
            relation_name = reference
        # Build and return a Relation object
        relation_object = Relation(
            name=relation_name,
            negate_field=negate_field,
            duration_modifier_operator=duration_modifier_operator,
            duration_modifier_time_value=duration_modifier_time_value
        )
        return relation_object, left_directed_relation

    @classmethod
    def _parse_sentence(cls, sentence_definition, variables_in_this_scope):
        """Parse the given sentence definition."""
        sentence_sublist = []
        # If it's a time sentence, parse it accordingly
        if sentence_definition.startswith('[') and sentence_definition.endswith(']'):
            # "Boolean time sentence" in the form of a "time operand list"
            for component in re.split("(/|&)", sentence_definition[1:-1]):
                if component in ("&", "/"):
                    sentence_sublist.append(component)
                    continue
                time_operand = component.strip()  # Ex: "T < 1700" or "T != 1400"
                _time_literal, operator, time_value = time_operand.split()
                time_sentence_object = TimeSentence(operator=operator, time_value=time_value)
                sentence_sublist.append(time_sentence_object)
            return sentence_sublist, variables_in_this_scope
        # It's not a time sentence, so move on
        components = sentence_definition[1:-1].split()  # Strip off parentheses
        if len(components) == 2:
            raw_subject, _raw_relations = components
            sentence_subject, variables_in_this_scope = cls._parse_variable_or_noun(
                reference=raw_subject,
                variables_in_this_scope=variables_in_this_scope
            )
            raw_relations = []
            for part in re.split("(/|&)", _raw_relations):
                if part:
                    raw_relations.append(part)
            for raw_relation in raw_relations:
                if not raw_relation.strip():
                    continue
                if raw_relation in ("&", "/"):
                    sentence_sublist.append(raw_relation)
                    continue
                sentence_relation, left_directed = cls._parse_relation(reference=raw_relation)
                sentence = Sentence(
                    sentence_subject=sentence_subject,
                    sentence_relation=sentence_relation,
                    sentence_object=None
                )
                sentence_sublist.append(sentence)
            return sentence_sublist, variables_in_this_scope
        raw_subject, *_raw_relations, raw_object = components
        sentence_subject, variables_in_this_scope = cls._parse_variable_or_noun(
            reference=raw_subject,
            variables_in_this_scope=variables_in_this_scope
        )
        sentence_object, variables_in_this_scope = cls._parse_variable_or_noun(
            reference=raw_object,
            variables_in_this_scope=variables_in_this_scope
        )
        # It's a sentence including multiple relations. We're going to construct multiple Sentence objects
        # to make it easier to evaluate them later on.
        raw_relations = []
        for raw_relation in _raw_relations:
            for part in re.split("(/|&)", raw_relation):
                if part:
                    raw_relations.append(part)
        for raw_relation in raw_relations:
            if not raw_relation.strip():
                continue
            if raw_relation in ("&", "/"):
                sentence_sublist.append(raw_relation)
                continue
            sentence_relation, left_directed = cls._parse_relation(reference=raw_relation)
            if left_directed:  # Swap sentence and object due to left-directed relation
                sentence = Sentence(
                    sentence_subject=sentence_object,
                    sentence_relation=sentence_relation,
                    sentence_object=sentence_subject
                )
            else:
                sentence = Sentence(
                    sentence_subject=sentence_subject,
                    sentence_relation=sentence_relation,
                    sentence_object=sentence_object
                )
            sentence_sublist.append(sentence)
        return sentence_sublist, variables_in_this_scope

    @classmethod
    def parse_lexical_expressions_file(cls, path_to_lexical_expressions_file):
        """Parse the given lexical-expressions file."""
        lexical_expressions_mapping = {}
        # Read in the lexical-expressions file
        lines = open(path_to_lexical_expressions_file).readlines()
        # Convert to uppercase
        lines = [line.upper() for line in lines if line.strip()]
        # Remove blank lines
        lines = [line.strip() for line in lines if line.strip()]
        # Remove comments
        lines = [line for line in lines if not line.lstrip().startswith('%')]
        # Parse each line
        for line in lines:
            try:
                noun_or_relation, lexical_expressions = line.split(':')
            except ValueError:
                raise Exception(f"Malformed lexical-expression definition: {line}")
            noun_or_relation = noun_or_relation.strip()
            lexical_expressions = lexical_expressions.strip()
            lexical_expressions = lexical_expressions.replace(', ', ',').split(',')
            lexical_expressions_mapping[noun_or_relation] = lexical_expressions
        return lexical_expressions_mapping
