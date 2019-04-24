"""A scrolling maze to explore. Collect all of the coins!

The goal of the this environment is to test generalization and symbol extraction for planning.


Todo list: (Ordered by importance)

# TODO(!!!)  Objective generator
    Generate a graph of objectives. Such as keys, doors, multiple keys for different doors.

# TODO(!!!)  Objective solver
    We need a deterministic solver to confirm that this map is actually solvable before dispatching to agent


# TODO(!!)  Dynamics objects
    Objects change shape, color per round

# TODO(!!)  Dynamic map size / walls

# TODO(!!)  OpenAI GyM Compatibility

# TODO(!!)  Dynamic background

# TODO(!)   Partial Viewport



Better Scrolly Maze is better than Scrolly Maze because it uses a much simpler
scrolling mechanism: cropping! As far as the pycolab engine is concerned, the
game world doesn't scroll at all: it just renders observations that are the size
of the entire map. Only later do "cropper" objects crop out a part of the
observation to give the impression of a moving world.

This cropping mechanism also makes it easier to derive multiple observations
from the same game, so the human user interface shows three views of the map at
once: a moving view that follows the player, another one that follows the
Patroller Sprite identified by the 'c' character, and a third that remains fixed
on a tantalisingly large hoard of gold coins, tempting the player to explore.

Regrettably, the cropper approach does mean that we have to give up the cool
starfield floating behind the map in Scrolly Maze. If you like the starfield a
lot, then Better Scrolly Maze isn't actually better.

Command-line usage: `better_scrolly_maze.py <level>`, where `<level>` is an
optional integer argument selecting Better Scrolly Maze levels 0, 1, or 2.

Keys: up, down, left, right - move. q - quit.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import curses
from PyQt5.QtCore import Qt
import sys

from pycolab import ascii_art
from pycolab import cropping
from pycolab import human_ui_qt
from pycolab import things as plab_things
from pycolab.prefab_parts import sprites as prefab_sprites


# pylint: disable=line-too-long
MAZES_ART = [
    # Each maze in MAZES_ART must have exactly one of the patroller sprites
    # 'a', 'b', and 'c'. I guess if you really don't want them in your maze, you
    # can always put them down in an unreachable part of the map or something.
    #
    # Make sure that the Player will have no way to "escape" the maze.
    #
    # Legend:
    #     '#': impassable walls.            'a': patroller A.
    #     '@': collectable coins.           'b': patroller B.
    #     'P': player starting location.    'c': patroller C.
    #     ' ': boring old maze floor.
    #
    # Finally, don't forget to update INITIAL_OFFSET and TEASER_CORNER if you
    # add or make substantial changes to a level.

    # Maze #0:
    ['#########################################################################################',
     '#                                                                                       #',
     '#                                                                                       #',
     '#       @                                                                @              #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#              P                                                                        #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#       a                                                                               #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                               @                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#                                                                                       #',
     '#########################################################################################'],

    # Maze #1
    ['##############################',
     '#                            #',
     '#   @   @   @   @   @   @    #',
     '#    @   @   @   @   @   @   #',
     '#     @   @   @   @   @   @  #',
     '#  @   @   @   @   @   @     #',
     '#   @   @   @   @   @   @    #',
     '#    @   @   @   @   @   @   #',
     '#                            #',
     '#########  a         #########',
     '##########        b ##########',
     '#                            #',
     '#   @   @   @   @   @   @    #',
     '#    @   @   @   @   @   @   #',
     '#     @   @   @   @   @   @  #',
     '#  @   @   @   @   @   @     #',
     '#   @   @   @   @   @   @    #',
     '#    @   @   @   @   @   @   #',
     '#                            #',
     '#######       c        #######',
     '#                            #',
     '#   @   @   @   @   @   @    #',
     '#    @   @   @   @   @   @   #',
     '#     @   @   @   @   @   @  #',
     '#  @   @   @   @   @   @     #',
     '#   @   @   @   @   @   @    #',
     '#    @   @   @   @   @   @   #',
     '#              P             #',
     '##############################'],

    # Maze #2
    ['                                                                                         ',
     '   ###################################################################################   ',
     '   #  @  @  @  @  @  @  @  @  @  @           P                                       #   ',
     '   #   ###########################################################################   #   ',
     '   # @ #                                                                         #   #   ',
     '   #   #                                                                         #   #   ',
     '   # @ #                    ######################################################   #   ',
     '   #   #                    #                                                        #   ',
     '   # @ #                    #   ######################################################   ',
     '   #   #                    #   #                                                        ',
     '   # @ #                    #   #                                                        ',
     '   #   #                    #   ######################################################   ',
     '   # @ #                    #                                                        #   ',
     '   #   #                    ######################################################   #   ',
     '   # @ #                                                                         #   #   ',
     '   #   #                                                                         #   #   ',
     '   # @ #                                            ##############################   #   ',
     '   #   #                                           ##                            #   #   ',
     '   # @ #                                           #      @@@@@      #########   #   #   ',
     '   #   #                                           #   @@@@@@@@@@@   #       #   #   #   ',
     '   # @ ###########                                ##@@@@@@@@@@@@@@@@@##      #   #   #   ',
     '   #   # @  @  @ #                               ##@@@@@@@@@@@@@@@@@@@##     #   #   #   ',
     '   # @ #  a      #                              ##@@@@@@@@Peyiang@@@@@@@@@@@@@##    #   #   #   ',
     '   #   #    b    #                             ##@@@@@@@@@@@@@@@@@@@@@@@##   #   #   #   ',
     '   # @ #      c  #                             ##@@@@@@@@@@@@@@@@@@@@@@@##   #   #   #   ',
     '   #   #######   #                              ##@@@@@@@@@@@@@@@@@@@@@##    #   #   #   ',
     '   # @  @  @     #                               ##@@@@@@@@@@@@@@@@@@@##     #       #   ',
     '   ###############                                #####################      #########   ',
     '                                                                                         '],
]
# pylint: enable=line-too-long


# The "teaser observations" (see docstring) have their top-left corners at these
# row, column maze locations. (The teaser window is 12 rows by 20 columns.)
TEASER_CORNER = [(3, 9),    # For level 0
                 (4, 5),    # For level 1
                 (16, 53)]  # For level 2

# For dramatic effect, none of the levels start the game with the first
# observation centred on the player; instead, the view in the window is shifted
# such that the player is this many rows, columns away from the centre.
STARTER_OFFSET = [(-2, -12),  # For level 0
                  (10, 0),    # For level 1
                  (-3, 0)]    # For level 2


def make_game(level):
  """Builds and returns a Better Scrolly Maze game for the selected level."""
  return ascii_art.ascii_art_to_game(
      MAZES_ART[level], what_lies_beneath=' ',
      sprites={
          'P': PlayerSprite,
          'a': PatrollerSprite,
          'b': PatrollerSprite,
          'c': PatrollerSprite},
      drapes={
          '@': CashDrape},
      update_schedule=['a', 'b', 'c', 'P', '@'],
      z_order='abc@P')


def make_croppers(level):
  """Builds and returns `ObservationCropper`s for the selected level.

  We make three croppers for each level: one centred on the player, one centred
  on one of the Patrollers (scary!), and one centred on a tantalising hoard of
  coins somewhere in the level (motivating!)

  Args:
    level: level to make `ObservationCropper`s for.

  Returns:
    a list of three `ObservationCropper`s.
  """
  return [
      # The player view.
      cropping.ScrollingCropper(rows=10, cols=30, to_track=['P'],
                                initial_offset=STARTER_OFFSET[level]),
      # The patroller view.
      cropping.ScrollingCropper(rows=7, cols=10, to_track=['c'],
                                pad_char=' ', scroll_margins=(None, 3)),
      # The teaser!
      cropping.FixedCropper(top_left_corner=TEASER_CORNER[level],
                            rows=12, cols=20, pad_char=' '),
  ]


class PlayerSprite(prefab_sprites.LargerObject):
  """A `Sprite` for our player, the maze explorer."""

  def __init__(self, corner, position, character):
    """Constructor: just tells `MazeWalker` we can't walk through walls."""

    # Example of a 5 x 5 diamond, Key: relative position to center, Value: RGB value
    img = {(-2, 0): (0, 0, 255),
                  (-1, -1): (0, 0, 255),
                  (-1, 1): (0, 0, 255),
                  (0, -2): (0, 0, 255),
                  (0, 2): (0, 0, 255),
                  (1, -1): (0, 0, 255),
                  (1, 1): (0, 0, 255),
                  (2, 0): (0, 0, 255),
                  }
    super(PlayerSprite, self).__init__(
        img, corner, position, character, impassable='#')

  def update(self, actions, board, layers, backdrop, things, the_plot):
    del backdrop, things, layers  # Unused

    if actions == 0:    # go upward?
      self._north(board, the_plot)
    elif actions == 1:  # go downward?
      self._south(board, the_plot)
    elif actions == 2:  # go leftward?
      self._west(board, the_plot)
    elif actions == 3:  # go rightward?
      self._east(board, the_plot)
    elif actions == 4:  # stay put? (Not strictly necessary.)
      self._stay(board, the_plot)
    if actions == 5:    # just quit?
      the_plot.terminate_episode()


class PatrollerSprite(prefab_sprites.LargerObject):
  """Wanders back and forth horizontally, killing the player on contact."""

  def __init__(self, corner, position, character):
    """Constructor: list impassables, initialise direction."""

    img = {(-2, 0): (255, 0, 0),
                  (-1, -1): (255, 0, 0),
                  (-1, 1): (255, 0, 0),
                  (0, -2): (255, 0, 0),
                  (0, 2): (255, 0, 0),
                  (1, -1): (255, 0, 0),
                  (1, 1): (255, 0, 0),
                  (2, 0): (255, 0, 0),
                  }

    super(PatrollerSprite, self).__init__(
        img, corner, position, character, impassable='#')
    # Choose our initial direction based on our character value.
    self._moving_east = False

  def update(self, actions, board, layers, backdrop, things, the_plot):
    del actions, backdrop  # Unused.

    # We only move once every two game iterations.
    if the_plot.frame % 2:
      self._stay(board, the_plot)  # Also not strictly necessary.
      return

    # If there is a wall next to us, we ought to switch direction.
    row, col = self.position
    if layers['#'][row, col-1]: self._moving_east = True
    if layers['#'][row, col+1]: self._moving_east = False

    # Make our move. If we're now in the same cell as the player, it's instant
    # game over!
    (self._east if self._moving_east else self._west)(board, the_plot)
    # if self.position == things['P'].position: the_plot.terminate_episode()
    if self.is_colliding(things['P']): the_plot.terminate_episode()


class CashDrape(plab_things.LargeDrape, plab_things.ILarge):
  """A `Drape` handling all of the coins.

  This Drape detects when a player traverses a coin, removing the coin and
  crediting the player for the collection. Terminates if all coins are gone.
  """
  def __init__(self, curtain, character):
    """Constructor: list impassables, initialise direction."""

    img = {(-2, 0): (0, 255, 0),
                  (-1, -1): (0, 255, 0),
                  (-1, 1): (0, 255, 0),
                  (0, -2): (0, 255, 0),
                  (0, 2): (0, 255, 0),
                  (1, -1): (0, 255, 0),
                  (1, 1): (0, 255, 0),
                  (2, 0): (0, 255, 0),
                  }


    super(CashDrape, self).__init__(
        img, curtain, character)

  def update(self, actions, board, layers, backdrop, things, the_plot):
    # If the player has reached a coin, credit one reward and remove the coin
    # from the scrolling pattern. If the player has obtained all coins, quit!
    player_pattern_position = things['P'].position

    for drape_coord in self.drape_list:
        if self.is_colliding(things['P'], drape_coord):
            the_plot.log('Coin collected at {}!'.format(player_pattern_position))
            the_plot.add_reward(100)
            self.curtain[drape_coord[0], drape_coord[1]] = False
            if not self.curtain.any(): the_plot.terminate_episode()
            break



def main(argv=()):
  level = int(argv[1]) if len(argv) > 1 else 0

  # Build a Better Scrolly Maze game.
  game = make_game(level)

  # Build the croppers we'll use to scroll around in it, etc.
  croppers = make_croppers(level)

  # Make a CursesUi to play it with.
  ui = human_ui_qt.HumanUI(
      rows = 46,
      cols = 89,

      keys_to_actions={Qt.Key_Up: 0, Qt.Key_Down: 1,
                       Qt.Key_Left: 2, Qt.Key_Right: 3,
                       -1: 4,
                       Qt.Key_Q: 5},
      delay=100,
      #croppers=level
  )

  # Let the game begin!
  ui.play(game)


if __name__ == '__main__':
  main(sys.argv)
