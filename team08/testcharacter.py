import os
import sys

sys.path.insert(0, '../bomberman')

import json
import random
from collections import deque

from entity import CharacterEntity  # type: ignore
from sensed_world import SensedWorld  # type: ignore


class TestCharacter(CharacterEntity):

    path_to_weights = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights.json")

    epoch   = 0
    weights = None

    gamma   = 0.9 # discount rate
    alpha   = 0.1 # learning rate
    epsilon = 0.1 # curiosity meter

    # previous feature state, reward, and q-state
    prev_feature_state = None
    prev_reward        = 0.0

    # counter for saving
    save_counter = 0

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
                        not(wrld.wall_at(cell[0] + nx, cell[1] + ny)                )
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
    def get_world_state(self, wrld):
        character_object = wrld.me(self)
        monster_cells    = set()
        bomb_cell        = None
        bomb_timer       = None
        explosion_cells  = set()
        wrld_state       = {}

        for monsters in wrld.monsters.values():
            for monster in monsters:
                monster_cells.add((monster.x, monster.y))

        for bomb_object in wrld.bombs.values():
            bomb_cell  = (bomb_object.x, bomb_object.y)
            bomb_timer = bomb_object.timer

        for explosion_cell in wrld.explosions.values():
            explosion_cells.add((explosion_cell.x, explosion_cell.y))

        wrld_state["character cell"]  = (character_object.x, character_object.y)
        wrld_state["exit cell"]       = wrld.exitcell
        wrld_state["monster cells"]   = monster_cells
        wrld_state["bomb cell"]       = bomb_cell
        wrld_state["bomb fuse"]       = wrld.bomb_time
        wrld_state["bomb timer"]      = bomb_timer
        wrld_state["explosion cells"] = explosion_cells
        wrld_state["explosion range"] = wrld.expl_range

        return(wrld_state)

    ###
    # wrld_state: relevant data from wrld fetched with get_world_state()
    #
    # >>> returns current and imminent explosion cells; time left down to which a cell is considered unsafe can be set with bomb_escape_time
    def get_dangerous_cells(self, wrld_state, wrld):
        bomb_escape_time       = 3

        bomb_cell              = wrld_state["bomb cell"]
        bomb_time              = wrld_state["bomb timer"]
        explosion_range        = wrld_state["explosion range"]
        dangerous_cells        = []

        dangerous_cells.extend(wrld_state["explosion cells"])

        if(bomb_cell): 
            dangerous_cells.append(bomb_cell)
        
            if(bomb_time <= bomb_escape_time):
                for x in range(1, explosion_range + 1): # Right of bomb                
                    # Add cells only if in world, break otherwise
                    if bomb_cell[0]+x < wrld.width(): dangerous_cells.append((bomb_cell[0]+x, bomb_cell[1]))
                    else: break
                    
                    # Add dangerous cell if at wall (explosion lingers in broken wall), then stop
                    if wrld.wall_at(bomb_cell[0] + x, bomb_cell[1]): break
                        
                for x in range(1, explosion_range + 1): # Left of bomb
                    if bomb_cell[0]-x >= 0: dangerous_cells.append((bomb_cell[0]-x, bomb_cell[1]))
                    else: break
                    
                    if wrld.wall_at(bomb_cell[0] - x, bomb_cell[1]): break
                    
                for y in range(1, explosion_range + 1): # Below bomb
                    if bomb_cell[1]+y < wrld.height(): dangerous_cells.append((bomb_cell[0], bomb_cell[1]+y))
                    else: break
                    
                    if wrld.wall_at(bomb_cell[0], bomb_cell[1]+y): break

                for y in range(1, explosion_range + 1): # Above bomb
                    if bomb_cell[1]-y >= 0: dangerous_cells.append((bomb_cell[0], bomb_cell[1]-y))
                    else: break
                    
                    if wrld.wall_at(bomb_cell[0], bomb_cell[1]-y): break

        return(dangerous_cells)

    ###
    # wrld         : the world
    # start_cell   : cell to start from
    # blocked_cells: cells to exclude from search
    #
    # >>> returns Look-Up Grid of reachable cell positions and distances from start cell using BFS, excluding given blocked cells
    def get_lug(self, wrld, start_cell, blocked_cells):
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

    ###
    # wrld      : the world
    # wrld_state: world state dictionary from get_world_state()
    #
    # >>> returns character's current legal actions, with actions being direction to move in and whether to place a bomb
    def get_legal_actions(self, wrld, wrld_state):
        neighbors     = self.get_neighbors_of_8(wrld, wrld_state["character cell"])
        bomb_ready    = wrld_state["bomb cell"] is None
        legal_actions = []

        for neighbor in neighbors:
            if(neighbor != wrld_state["bomb cell"]):
                legal_actions.append((neighbor, False))
                if(bomb_ready): legal_actions.append((neighbor, True))

        return(legal_actions)

    ###
    # wrld  : the world
    # action: action to try out
    #
    # >>> returns the hypothetical result of acting out the given action in the current world state as a hypothetical resulting world and its corresponding events
    def do_hypth_action(self, wrld, action):
        (target_cell, place_bomb) = action
        hypth_wrld                = SensedWorld.from_world(wrld)
        hypth_character           = hypth_wrld.me(self)

        hypth_character.move(target_cell[0] - hypth_character.x, target_cell[1] - hypth_character.y)
        if(place_bomb): hypth_character.place_bomb()

        return(hypth_wrld.next())

    ###
    # events: world events
    #
    # >>> returns corresponding rewards for all events given
    def get_reward(self, events):
        reward = -0.1

        for event in events:
            if  (event.tpe == event.BOMB_HIT_WALL)                   : reward += 5
            elif(event.tpe == event.BOMB_HIT_MONSTER)                : reward += 2
            elif(
                 (event.tpe == event.BOMB_HIT_CHARACTER)          or
                 (event.tpe == event.CHARACTER_KILLED_BY_MONSTER)
                )                                                    : return(-10, True)
            elif(event.tpe == event.CHARACTER_FOUND_EXIT)            : return( 10 , True)

        return(reward, False)

    ###
    # hypth_wrld: hypothetical / copied world
    #
    # >>> returns feature values given hypothetical world state
    def extract_features(self, hypth_wrld, bomb_placed):
        hypth_wrld_state = self.get_world_state(hypth_wrld)
        max_distance     = max(hypth_wrld.width(), hypth_wrld.height()) - 1
        character_cell   = hypth_wrld_state["character cell"]
        exit_cell        = hypth_wrld_state["exit cell"]
        dangerous_cells  = self.get_dangerous_cells(hypth_wrld_state, hypth_wrld)
        lookup_grid      = self.get_lug(hypth_wrld, character_cell, dangerous_cells)
        features         = {}

        features["bias"]                      = 1.0
        features["exit distance"]             = (min(lookup_grid[exit_cell] / max_distance, 1.0))                                                          if   \
                                                (exit_cell in lookup_grid)                                                                                 else \
                                                (min(max(abs(character_cell[0] - exit_cell[0]), abs(character_cell[1] - exit_cell[1])) / max_distance, 1.0))
        features["nearest monster distance"]  = 1.0

        for monster_cell in hypth_wrld_state["monster cells"]:
            if((monster_cell in lookup_grid) and ((min(lookup_grid[monster_cell] / max_distance, 1.0)) < features["nearest monster distance"])):
                monster_distance                     = lookup_grid[monster_cell]
                features["nearest monster distance"] = min(monster_distance / max_distance, 1.0)

        features["bomb placed"]               = (1.0) if (bomb_placed) else (0.0)

        features["in danger"]                 = 0.0

        if(character_cell in dangerous_cells):
            bomb_timer = hypth_wrld_state["bomb timer"]

            if(bomb_timer is None): features["in danger"] = 1.0
            else                  : features["in danger"] = 1.0 - (bomb_timer / hypth_wrld_state["bomb fuse"])

        return(features)

    ###
    # feature_state: dictionary of features
    #
    # >>> returns q state value using given features values and weights
    def get_q_state(self, feature_state):
        return(
               (self.weights["bias"]                     * feature_state["bias"]                    ) +
               (self.weights["exit distance"]            * feature_state["exit distance"]           ) +
               (self.weights["nearest monster distance"] * feature_state["nearest monster distance"]) +
               (self.weights["bomb placed"]              * feature_state["bomb placed"]             ) +
               (self.weights["in danger"]                * feature_state["in danger"]               )
              )

    ###
    # wrld         : the world
    # legal_actions: actions that can be performed, not necessarily safe
    #
    # >>> returns a list of action scores with (action, q-state, features, reward)
    def get_action_scores(self, wrld, legal_actions):
        action_scores = []

        for action in legal_actions:
            (hypth_wrld, hypth_events) = self.do_hypth_action(wrld, action)
            (reward    , done)         = self.get_reward(hypth_events)

            if(hypth_wrld.me(self) is None): 
                feature_state = self.extract_features(wrld, action[1])

                if(done and (reward < 0)): feature_state["in danger"]     = 1.0
                else                     :feature_state["exit distance"]  = 0.0

            else: feature_state = self.extract_features(hypth_wrld, action[1])

            q_state = self.get_q_state(feature_state)
            action_scores.append((action, q_state, feature_state, reward, done))

        return(action_scores)

    ###
    # scored_actions: list of scored actions [(action, q-state, features, reward), ...]
    #
    # >>> returns chosen action taking epsilon value into account and breaking best-q-state scored action ties randomly
    def choose_action(self, scored_actions):
        pick_best_scored_action = random.random() > self.epsilon
        best_q_state            = float('-inf')
        best_scored_actions     = []
        chosen_scored_action    = (None, float('-inf'), None, None)

        if(pick_best_scored_action):
            for scored_action in scored_actions:
                best_q_state = max(best_q_state, scored_action[1])

            for scored_action in scored_actions:
                if(scored_action[1] == best_q_state): best_scored_actions.append(scored_action)

            chosen_scored_action = random.choice(best_scored_actions)

        else: chosen_scored_action = random.choice(scored_actions)

        return(chosen_scored_action)

    ###
    # >>> loads saved external epoch and weights into class epoch and weight variables from JSON file
    def load_weights(self):
        with open(self.path_to_weights, "r") as file:
            data = json.load(file)

            self.epoch   = data["epoch"]
            self.weights = data["weights"]

    ###
    # >>> updates external JSON file epoch and weights with class epoch and weights
    def save_weights(self):
        with open(self.path_to_weights, "w") as file:
            json.dump({ "epoch": self.epoch, "weights": self.weights }, file, indent=4)

    ###
    # best_next_q_state: best next q-state
    # done             : whether the character has died/won, or is still playing
    #
    # >>> updates in-game weights with previous features, q-state, and reward values, along with alpha and gamma
    def update_weights(self, best_next_score):
        delta = self.prev_reward + (self.gamma * best_next_score) - self.get_q_state(self.prev_feature_state)

        self.weights["bias"]                     += self.alpha * delta * self.prev_feature_state["bias"]
        self.weights["exit distance"]            += self.alpha * delta * self.prev_feature_state["exit distance"]
        self.weights["nearest monster distance"] += self.alpha * delta * self.prev_feature_state["nearest monster distance"]
        self.weights["bomb placed"]              += self.alpha * delta * self.prev_feature_state["bomb placed"]
        self.weights["in danger"]                += self.alpha * delta * self.prev_feature_state["in danger"]

# --- Main Loop --------------------------------------------------------------------------------------------------------------------------------------------------- #

    # baptism by fire
    def do(self, wrld):
        best_next_score = float('-inf')

        if(self.weights is None):
            self.load_weights()
            self.epoch += 1

        wrld_state     = self.get_world_state(wrld)
        legal_actions  = self.get_legal_actions(wrld, wrld_state)
        scored_actions = self.get_action_scores(wrld, legal_actions)

        if(self.prev_feature_state is not None):
            for scored_action in scored_actions: best_next_score = max(best_next_score, scored_action[1])
            self.update_weights(best_next_score)

        chosen_action = self.choose_action(scored_actions)
        (the_play, to_bomb_or_not_to_bomb) = chosen_action[0]
        feature_state                      = chosen_action[2]
        reward                             = chosen_action[3]
        done                               = chosen_action[4]

        self.prev_feature_state = feature_state
        self.prev_reward        = reward

        if(done):
            self.update_weights(0.0)
            self.save_weights()

        if(self.save_counter >= 5):
            self.save_counter = 0
            self.save_weights()

        self.save_counter += 1

        # NOTE: DEBUGGING FINAL MOVE
        print(f"Moving to ({the_play})")

        self.move(the_play[0] - self.x, the_play[1] - self.y)
        if(to_bomb_or_not_to_bomb): self.place_bomb()
