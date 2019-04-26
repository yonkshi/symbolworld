'''
CONFIG FILE FOR SYMBOLIC WORLD
'''

# Grid options

GRID_SIZE = 50
GRID_SIZE_VAR = 0  # +/- variation

# Generation Control

NUM_GOALS = 2
NUM_GOALS_VAR = 0 # +/- variation

NUM_ADVERSARIES = 1
NUM_ADVERSARIES_VAR = 0


# Ensure there are no other objects within N blocks nearby it. Should be 2x the size of normal object
# Temporary solution, might implement more robust system later
SAFETY_BOX = 6


# Human UI config

CELL_PIXELS = 1