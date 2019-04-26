from pycolab.config import *
import numpy as np
import sys


_C_BACKGROUND = ord(' ')
_C_WALLS      = ord('#')
_C_PLAYER   = ord('P')
_C_ADVERSARY = ord('a')
_C_GOAL = ord('@')
_C_KEY = ord('K')

def generate_level(seed=None):
    np.random.seed(seed)
    gridsize = sample(GRID_SIZE, GRID_SIZE_VAR)
    grid = np.ones((gridsize, gridsize), dtype='int8')
    grid *= _C_BACKGROUND

    numgoals = sample(NUM_GOALS, NUM_GOALS_VAR)
    numadversaries = sample(NUM_ADVERSARIES, NUM_ADVERSARIES_VAR)

    # Generate bounding wall
    grid[0, :] = _C_WALLS
    grid[-1, :] = _C_WALLS
    grid[:, 0] = _C_WALLS
    grid[:, -1] = _C_WALLS


    def try_gen_object():
        ''' Try and place and object on to the board '''

        # Sample 100 coordinates to try
        potential_coords = np.random.randint(0, gridsize+1, size=(100, 2))
        for row , col in potential_coords: # Try to place object 100 times
            if is_safe_to_place(grid, row, col):
                return row, col
        # Failed to place object
        raise AssertionError('Failed to place object')


    # Generat player
    row, col = try_gen_object()
    grid[row, col] = _C_PLAYER

    # Generate adversaries
    for _ in range(numadversaries):
        row, col = try_gen_object()
        grid[row, col] = _C_ADVERSARY

    # Generate keys, same number as goals
    for _ in range(numgoals):
        row, col = try_gen_object()
        grid[row, col] = _C_KEY

    # Generate goals
    for _ in range(numgoals):
        row, col = try_gen_object()
        grid[row, col] = _C_GOAL

    return np2str(grid)

def is_safe_to_place(grid, row, col):
    '''
    Check tentative coordinates surrounding area, make sure
    :param row:
    :param col:
    :param gridsize:
    :return:
    '''
    # Boundary check
    gridsize = grid.shape[0]
    if row - SAFETY_BOX < 0 or row + SAFETY_BOX + 1 > gridsize: return False
    if col - SAFETY_BOX < 0 or col + SAFETY_BOX + 1 > gridsize: return False

    i = np.arange(row - SAFETY_BOX, row + SAFETY_BOX + 1) # Account for last idx
    j = np.arange(col - SAFETY_BOX, col + SAFETY_BOX + 1)
    mesh_idx = np.ix_(i, j)

    surrouding = np.sum(grid[mesh_idx] - _C_BACKGROUND) # If everything is background character, then sum should be 0

    return surrouding == 0



def np2str(grid):

    return [ "".join([chr(char) for char in row]) for row in grid]


def sample(mean, var):
    '''
    Uniformly samples from (mean - var) to (mean + var)
    :param mean: mean
    :param var: var
    :return:
    '''
    assert mean - var >= 0, 'Variance cannot be greater than mean'
    return np.random.randint(mean-var, mean+var + 1)


if __name__ == '__main__':
    main(sys.argv)
