import math
import sys

sys.path.insert(0, '../bomberman')

import numpy as np
from entity import CharacterEntity  # type: ignore


class TestCharacter(CharacterEntity):

    path_to_weights = "./weights.json"

    epoch   = 0
    weights = {}

    gamma   = 0.9
    alpha   = 0.5
    epsilon = 0.5

    prev_character_state = {}
    prev_reward          = 0.0

    # return list of cells around and including given cell
    # only exclude walls
    def get_neighbors_of_8(self, wrld, cell):
        pass

    # return dictionary with:
    #  - character cell
    #  - exit cell
    #  - monster cells
    #  - bomb cells and detonation time(s)
    #  - explosion cells
    def get_wrld_state(self, wrld):
        pass

    # return list of current and imminent bomb and explosion cells 
    def get_dangerous_cells(self, wrld, wrld_state):
        pass

    # return dictionary with reachable cells, excluding blocked cells, as keys and distances as values
    def bfs(self, wrld, start_cell, blocked_cells):
        pass

    # return a list of legal cells and whether a bomb can be placed for each one
    def legal_actions(self, wrld, wrld_state):
        pass

    # return the hypothetical result of applying a given action in the given world
    def do_hypth_action(self, wrld, action):
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

    # returns a reward value given hypothetical world events and cost of living
    def get_reward(self, hypth_wrld, events):
        pass

    # update the in-game/run weights
    def update_weights(self, best_next_q_state):
        pass

    # return the chosen action, which will either be the best one according to what is known, or a random one depending on how high/low epsilon is
    def get_action(self, actions):
        pass

    # get the weight stored in the external JSON file
    def get_weights(self):
        pass

    # update th weights stored in the external JSON file
    def save_weights(self):
        pass

# --- Main Loop --------------------------------------------------------------------------------------------------------------------------------------------------- #

    # load epoch and weights if empty
    # call action_scores()
    # if the character has already moved at least once (meaning the prev_ variables aren't empty), update the in-game weights
    # call get_action()
    # update the prev_ variables
    # actually move + place or don't place a bomb
    # when the game ends, update the external weights.  Still need to decide how/when that should be handled
    def do(self, wrld): 
        pass
