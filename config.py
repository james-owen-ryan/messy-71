import os
import time


# Alters the verbosity of output, which is especially useful during debugging. 0 = nothing; 1 = story only;
# 2 = minimal debug printout; 3 = extensive debug printout.
VERBOSITY = 1
# By default, the random seed is the current UNIX time. To set the seed, change _RANDOM_SEED
# to your desired seed. To change back to the current UNIX time, revert _RANDOM_SEED to None.
_RANDOM_SEED = None
RANDOM_SEED = _RANDOM_SEED or int(round(time.time()))
# The diegetic time of day at which each simulation instance begins. Following Klein et al. (1971),
# this is expressed as an integer representing a time in 24-hour-clock notation. For instance,
# 1910 is 7:10 PM, whereas 2060 is not a valid time.
START_TIME = 1700
# The length, in minutes, of each simulated timestep. Klein et al. (1971) sets this to 10 minutes.
TIMESTEP = 10
# The number of time frames to simulate in total
NUMBER_OF_TIME_FRAMES = 30
# In MESSY-71, the evaluation of an action condition increments or decrements the probability of that
# action being taken. Following Klein et al. (1971), our implementation allows an author to associate
# conditions with extreme probabilities increments that will immediately force an action to be taken
# or to be abandoned. Klein used -10 and 10 as the respective thresholds for such short-circuiting.
SHORT_CIRCUIT_PROBABILITY_INCREMENT_ABSOLUTE_THRESHOLD = 10.0
# This parameter determines whether entities will be allowed to appear multiple times in the bindings
# for an action. For instance,
ALLOW_DUPLICATE_ENTITIES_IN_VARIABLE_BINDINGS = True
# Paths for the three procedural-content files that drive simulation: a rules file containing definitions
# for all of the simulation rules; a file containing initial conditions for the simulated storyworld; and
# a file containing lexical expressions for the entities defined in the preceding files (this file is used
# to drive the "narrative style control monitor" that renders the surface expression of a story). We have
# included example files created by Theresa Chen and Piper Welch.
PATH_TO_RULES_DIRECTORY = "content"
PATH_TO_RULES_FILE = os.path.join(PATH_TO_RULES_DIRECTORY, "murder_story_rules.txt")
PATH_TO_INITIAL_CONDITIONS_FILE = os.path.join(PATH_TO_RULES_DIRECTORY, "murder_story_initial_conditions.txt")
PATH_TO_LEXICAL_EXPRESSIONS_FILE = os.path.join(PATH_TO_RULES_DIRECTORY, "murder_story_lexical_expression_lists.txt")
# There are two output modes in this implementation of MESSY-71: one that outputs to stdout, and another
# that outputs to a file. To engage the latter mode, set OUTPUT_TO_FILE to True and update the LOG_FILE
# path as needed.
OUTPUT_TO_FILE = False
LOG_FILE = 'console.log'
