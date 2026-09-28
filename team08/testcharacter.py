import math
import sys

sys.path.insert(0, '../bomberman')

import numpy as np
from entity import CharacterEntity  # type: ignore


class TestCharacter(CharacterEntity):
# --- General-Purpose --------------------------------------------------------------------------------------------------------------------------------------------- #
    
    ##
    # cell_a (x, y): first cell
    # cell_b (x, y): second cell
    #
    # >>> returns straight-line distance between given cells
    def euclid_dist(self, cell_a, cell_b):
        return(
            math.sqrt(
                (cell_a[0] - cell_b[0])**2 + 
                (cell_a[1] - cell_b[1])**2
                )
            )

    ##
    # wrld [SensedWorld]: the world
    # cell (x, y)       : cell to look around for viable neighbors
    #
    # >>> returns list of valid cells to go to
    def get_neighbors_8(self, wrld, cell):
        cells = []

        for nx in [-1, 0, 1]:
            if (
                (cell[0] + nx >= 0)           and
                (cell[0] + nx <  wrld.width())
                ):
                for ny in [-1, 0, 1]:
                    if (
                        (
                            (cell[1] + ny >= 0)             and
                            (cell[1] + ny <  wrld.height())

                        ) and not(
                            wrld.wall_at(cell[0] + nx, cell[1] + ny)

                        ) 
                       ):
                            cells.append((cell[0] + nx, cell[1] + ny))
        return(cells)

    ##
    # wrld [SensedWorld]: given world state
    #
    # >>> returns list of monster positions found
    def find_monsters(self, wrld):
        monsters = []

        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.monsters_at(x, y)): monsters.append((x, y))

        return(monsters)

# --- Approximate Q-Learning -------------------------------------------------------------------------------------------------------------------------------------- #
# 
# stuff goes here
#
# Overview
# - Q(s, a) = \Sigma_{i}^{n}(w_{i}f_{i}(s, a))
# - observe current state
# - choose action (be super greedy)
# - get target
# - get error
# - update weights
# - "one must imagine Sisyphus happy" ad infinitum
#
# Parameters that will matter
# - \alpha   (learning rate)
# - \gamma   (discount rate)
# - \epsilon (exploration rate / curious George meter)
#
# Persistent data
# - consider final update and reward after game ends
# - weights can easily be written to an external file on each update/run (JSON/YAML/etc.)
# - differentiate between training and testing runs
# - keep checkpoints of good weights
# - keep a record of weights across time
#

# --- Main Loop --------------------------------------------------------------------------------------------------------------------------------------------------- #

    ##
    # wrld: world state
    #
    # >>> actions to be completed in a timestep of gameplay
    def do(self, wrld): 
        pass
