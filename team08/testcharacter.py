import math
import sys

sys.path.insert(0, '../bomberman')

from collections import deque

import numpy as np
from entity import CharacterEntity  # type: ignore


class TestCharacter(CharacterEntity):

    path_to_weights = "./weights.json"

    epoch   = 0
    weights = {}

    gamma   = 0.9 # discount rate
    alpha   = 0.5 # learning rate
    epsilon = 0.1 # curiosity meter

    # previous feature state and reward
    prev_character_state = {}
    prev_reward          = 0.0

    ###
    # wrld: the world
    # cell: cell to find neighbors around
    #
    # >>> returns in-bounds cells around given cell that aren't walls
    def get_neighbors_of_8(self, wrld, cell):
        cells = []

        for nx in [-1, 0, 1]:
            if (
                (cell[0] + nx >= 0)            and
                (cell[0] + nx <  wrld.width())
               ):
                for ny in [-1, 0, 1]:
                    if (
                           (((cell[1] + ny >= 0) and (cell[1] + ny) < wrld.height())) and
                        not(wrld.wall_at(cell[0] + nx, cell[1] + ny))
                       ):
                        cells.append((cell[0] + nx, cell[1] + ny))
        return(cells)

    ###
    # wrld: the world
    #
    # >>> returns dictionary with:
    #  - character cell
    #  - exit cell
    #  - monster cells
    #  - bomb cell
    #  - bomb timer
    #  - explosion cells
    #  - explosion range
    def get_wrld_state(self, wrld):
        character_object = wrld.me(self)
        monster_cells    = set()
        bomb_cell        = ()
        bomb_timer       = 0
        explosion_cells  = set()
        wrld_state       = {}

        for monsters in wrld.monsters.values():
            for monster in monsters:
                monster_cells.add((monster.x, monster.y))

        for bomb_object in wrld.bombs.values():
            bomb_cell  = (bomb_object.x, bomb_object.y)
            bomb_timer = bomb_object.timer

        for explosion_cell in wrld.explosions.values(): explosion_cells.add((explosion_cell.x, explosion_cell.y))

        wrld_state["character"]       = (character_object.x, character_object.y)
        wrld_state["exit_cell"]       = wrld.exitcell
        wrld_state["monsters"]        = monster_cells
        wrld_state["bomb"]            = bomb_cell
        wrld_state["bomb timer"]      = bomb_timer
        wrld_state["explosion cells"] = wrld.explosions
        wrld_state["explosion range"] = wrld.expl_range

        return(wrld_state)

    ###
    # wrld_state: relevant data from wrld fetched with get_wrld_state()
    #
    # >>> returns current and imminent explosion cells; time left down to which a cell is considered unsafe can be set with bomb_escape_time
    def get_dangerous_cells(self, wrld_state):
        bomb_escape_time       = 3

        bomb_cell              = wrld_state["bomb"]
        bomb_time              = wrld_state["bomb timer"]
        explosion_range        = wrld_state["explosion range"]
        dangerous_cells        = []

        dangerous_cells.extend(wrld_state["explosion cells"])
        if(bomb_cell): dangerous_cells.append(bomb_cell)

        if(bomb_cell and (bomb_time <= bomb_escape_time)):
            for x in range(2 * explosion_range + 1):
                if((x - explosion_range) != 0): dangerous_cells.append(((bomb_cell[0] + (x - explosion_range)),  bomb_cell[1]                          ))

            for y in range(2 * explosion_range + 1):
                if((y - explosion_range) != 0): dangerous_cells.append( (bomb_cell[0]                         , (bomb_cell[1] + (y - explosion_range))))

        return(dangerous_cells)

    ###
    # wrld         : the world
    # start_cell   : cell to start from
    # blocked_cells: cells to exclude from search
    #
    # >>> returns Look-Up Grid of reachable cell positions and distances from start cell
    def bfs_lug(self, wrld, start_cell, blocked_cells):
        blocked_cells_set = set(blocked_cells)
        blocked_cells_set.discard(start_cell)

        cell_distances = {start_cell: 0}
        frontier       = deque([start_cell])

        while frontier:
            current_cell  = frontier.popleft()
            next_distance = cell_distances[current_cell] + 1

            for neighbor in self.get_neighbors_of_8(wrld, current_cell):
                if not((neighbor in blocked_cells_set) or (neighbor in cell_distances)):
                    cell_distances[neighbor] = next_distance
                    frontier.append(neighbor)

        return(cell_distances)

    # return a list of legal cells and whether a bomb can be placed for each one
    def legal_actions(self, wrld, wrld_state):
        pass

    # return the hypothetical result of applying a given action in the given world
    def do_hypth_action(self, wrld, action):
        pass

    # returns a reward value given hypothetical world events and cost of living
    def get_reward(self, hypth_wrld, events):
        pass

    # return a dictionary with feature names as keys and values as values
    def extract_features(self, hypth_wrld, events):
        pass

    # return the result of applying the weighted sum of all features values
    def q_state(self, character_state):
        pass

    # returns a list of actiones with their respective scores
    def action_scores(self, wrld):
        pass

    # return the chosen action, which will either be the best one according to what is known, or a random one depending on how high/low epsilon is
    def choose_action(self, actions):
        pass

    # get the weight stored in the external JSON file
    def get_weights(self):
        pass

    # update th weights stored in the external JSON file
    def save_weights(self):
        pass

    # update the in-game/run weights
    def update_weights(self, best_next_q_state):
        pass

# --- Main Loop --------------------------------------------------------------------------------------------------------------------------------------------------- #

    # load epoch and weights if empty
    # call action_scores()
    # if the character has already moved at least once (meaning the prev_ variables aren't empty), update the in-game weights
    # call choose_action()
    # update the prev_ variables
    # actually move + place or don't place a bomb
    # when the game ends, update the external weights.  Still need to decide how/when that should be handled
    def do(self, wrld): 
        wrld_state = self.get_wrld_state(wrld)

        start_cell    = (self.x, self.y)
        blocked_cells = self.get_dangerous_cells(wrld_state)

        print(self.bfs_lut(wrld, start_cell, blocked_cells))
