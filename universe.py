import config
from utils import red, green, blue, yellow
if config.OUTPUT_TO_FILE:
    import sys
    sys.stdout = open(config.LOG_FILE, 'a')


class Universe:
    """A stochastically modifiable semantic model of an arbitrary universe (see Klein 1971)."""

    def __init__(self):
        """Initialize a Universe object."""
        self.network = []  # A semantic network containing triples
        self.history = {}  # Maps previous plot times to the states of the modelled universe at those times
        self.queue = []  # A list of Triple objects to be added to the network next time frame
        self.time = config.START_TIME  # An integer representing 24-hour time, e.g., 1700 for 5pm
        self.time_since_start = 0  # An integer representing how many minutes have passed since the universe start time
        self.classes = {}  # Maps class names to nouns in that class
        self._load_initial_conditions()  # Populates self.network with initial triples
        # Print out initial triples
        if config.VERBOSITY >= 1:
            print(yellow(f"\t{self.time}"))
            for triple in self.network:
                print(blue(triple))

    def __str__(self):
        """Return string representation."""
        return "A Stochastically Modifiable Semantic Universe"

    def __repr__(self):
        """Return string representation."""
        return self.__str__()

    def _load_initial_conditions(self):
        """Load the initial conditions of this universe."""
        lines = open(config.PATH_TO_INITIAL_CONDITIONS_FILE).readlines()
        for line in lines:
            if not line.strip():
                continue
            if line.startswith("%"):
                # Ignore comment
                continue
            line = line.upper()
            while '\t\t' in line:
                line = line.replace('\t\t', '\t')
            if line.startswith("CLASS."):
                class_name, members = line.split('\t')
                class_name = class_name.split("CLASS.")[1].strip()
                if class_name not in self.classes:
                    self.classes[class_name.strip()] = []
                for member in members.split(','):
                    if member.strip().startswith('CLASS.'):
                        referenced_class_name = member.strip().split("CLASS.")[1]
                        self.classes[class_name] += self.classes[referenced_class_name]
                    else:
                        self.classes[class_name].append(member.strip())
                continue
            subject, content = line.split('\t')
            relations = content.split(',')
            for relation in relations:
                relation, *optional_object = relation.split()
                subject = subject.strip()
                relation = relation.strip()
                optional_object = optional_object[0].strip() if optional_object else None
                triple = Triple(
                    triple_subject=subject,
                    triple_relation=relation,
                    triple_object=optional_object,
                    time_frame=self.time,
                    time_since_start=self.time_since_start
                )
                self.network.append(triple)

    def match(self, triple_subject, triple_relation, triple_object):
        """Return whether the given triple matches against the current universe network."""
        for triple in self.network:
            if triple.subject != triple_subject:
                continue
            if triple.object != triple_object:
                continue
            if triple.relation != triple_relation.name:
                continue
            if triple_relation.duration_modifier_operator:
                if triple_relation.duration_modifier_operator == '=':
                    if triple_relation.duration_modifier_time_value != self.time_in_network(triple=triple):
                        continue
                elif triple_relation.duration_modifier_operator == '>':
                    if triple_relation.duration_modifier_time_value <= self.time_in_network(triple=triple):
                        continue
                elif triple_relation.duration_modifier_operator == '<':
                    if triple_relation.duration_modifier_time_value >= self.time_in_network(triple=triple):
                        continue
                elif triple_relation.duration_modifier_operator == '!=':
                    if triple_relation.duration_modifier_time_value == self.time_in_network(triple=triple):
                        continue
            return True if not triple_relation.negate_field else False
        return False if not triple_relation.negate_field else True

    def queue_triples(self, triples):
        """Queue the given triples to be added to the network next time frame."""
        self.queue += triples

    def update(self):
        """Add all the queued triples to the current network."""
        if config.VERBOSITY >= 1:
            print(yellow(f"\n\t{self.time}"))
        for triple_subject, triple_relation, triple_object in self.queue:
            for existing_triple in list(self.network):
                if existing_triple.subject != triple_subject:
                    continue
                if existing_triple.relation != triple_relation.name:
                    continue
                if existing_triple.object != triple_object:
                    continue
                if config.VERBOSITY >= 1:
                    if triple_relation.negate_field:
                        if not config.OUTPUT_TO_FILE:
                            print(red(f"{existing_triple}"))
                        else:
                            print(red(f"(DELETED) {existing_triple}"))
                self.network.remove(existing_triple)
            if not triple_relation.negate_field:
                # Note that this may just be replacing the one we just removed (to update the time frame added)
                new_triple = Triple(
                    triple_subject=triple_subject,
                    triple_relation=triple_relation.name,
                    triple_object=triple_object,
                    time_frame=self.time,
                    time_since_start=self.time_since_start
                )
                if config.VERBOSITY >= 1:
                    print(blue(new_triple))
                self.network.append(new_triple)
        if config.VERBOSITY >= 1:
            print()
        self.queue = []

    def time_in_network(self, triple):
        """Return the number of minutes since the given triple was last added to the network."""
        return self.time_since_start - triple.time_since_start


class Triple:
    """A triple in a semantic network."""

    current_id = 0

    def __init__(self, triple_subject, triple_relation, triple_object, time_frame, time_since_start):
        """Initialize a Triple object."""
        self.id = Triple.current_id
        Triple.current_id += 1
        self.subject = triple_subject
        self.relation = triple_relation
        self.object = triple_object
        self.time_frame = time_frame  # The plot time at which this triple was (last) added to the network
        self.time_since_start = time_since_start
        self.initial = self.time_frame == config.START_TIME

    def __str__(self):
        """Return string representation."""
        if self.object:
            return f"{self.subject} {self.relation} {self.object}"
        return f"{self.subject} {self.relation}"

    def __repr__(self):
        """Return string representation."""
        return self.__str__()
