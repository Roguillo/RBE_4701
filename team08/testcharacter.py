# This is necessary to find the main code
import sys
import math
import random
from queue import PriorityQueue
from collections import deque
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from sensed_world import SensedWorld 
from colorama import Fore, Back
import os
import json

class TestCharacter(CharacterEntity):

    weights = []

    path_to_weights = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights3.json")
    path_to_weightBackups = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights3_backup.json")

    wE = 1
    wM = -2
    wX = -5
    wB = -4
    wW = 3

    epoch   = 0
    weights = None

    gamma   = 0.9 # discount rate
    alpha   = 0.1 # learning rate
    epsilon = 0.1 # curiosity meter

    # previous feature state, reward, and q-state
    prev_feature_state = None
    prev_reward        = 0.0
    prev_q_state       = 0.0

    checkpoint = 0


    curiosity = 0.3

    rows, cols = (8*19, 9)
    qValues = [[0] * 9 for _ in range(rows)]

    monsterLastLocation = (9, 3)
    monsterLastDistance = 1.0



    def find_exit(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.exit_at(x, y)): return((x, y))

        return(None)

    def find_monster(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.monsters_at(x, y)): return((x, y))

        return(None)

    def find_monster_path(self, m, wrld):
        path = []
        (dx, dy) = (m.x - self.monsterLastLocation[0], m.y - self.monsterLastLocation[1])
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                for i in range(1,8):
                    px = m.x + (dx*i)
                    py = m.y + (dy*i)
                    if not (0 <= px < wrld.width() and 0 <= py < wrld.height()) or wrld.wall_at(px, py):
                        break
                    else :
                        path.append([px, py])

        return(path)

    def find_bomb(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.bomb_at(x, y)): return((x, y))

        return(None)

    def find_explosion(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.explosion_at(x, y)): return((x, y))

        return(None)
    
    def get_explosion_cells(self, wrld, bomb):
        positions = []

        dir = [[1,0],[0,1],[-1,0],[0,-1]]
        for d in dir:
            for i in range(1,6):
                px = bomb[0] + (d[0]*i)
                py = bomb[1] + (d[1]*i)
                if not (0 <= px < wrld.width() and 0 <= py < wrld.height()) or wrld.wall_at(px, py):
                    break
                else :
                    positions.append([px, py])
        return positions

    def nextToCorner(self, m, wrld):
        wallCount = 0
        for dx in [-1, 1]:
            # Loop through delta y
            for dy in [-1, 1]:
            # Avoid out-of-bound indexing
                diagonal = (m[0] + dx, m[1] + dy)
                horizontal = (m[0] + dx, m[1])
                vertical = (m[0], m[1] + dy)

                if ((0 > diagonal[0] or diagonal[0] >= 8) or (0 > diagonal[1] or diagonal[1] >= 18)) and not wrld.wall_at(diagonal[0], diagonal[1]):
                    continue

                # Horizontal side: either out of bounds or a wall
                print(horizontal)
                horizontal_blocked = (
                    (0 > horizontal[0] or horizontal[0] >= 8) or
                    wrld.wall_at(horizontal[0], horizontal[1])
                )

                # Vertical side: either out of bounds or a wall
                print(vertical)
                vertical_blocked = (
                    (0 > vertical[1] or vertical[1] >= 18) or
                    wrld.wall_at(vertical[0], vertical[1])
                )

                if horizontal_blocked and vertical_blocked:
                    wallCount += 1                
                        
        return wallCount


    def numWallInRow(self, y, wrld):
        count = 0
        for x in range(wrld.width()):
            if wrld.wall_at(x, y):
                count +=1
                    
                
        return count

    def get_pos_moves(self, m, wrld):
        pos_Smoves = []
        if self.find_bomb(wrld) is None:
            pos_Smoves.append([0, 0])
        curr_sMove = 0
        for dx in [-1, 0, 1]:
            # Avoid out-of-bound indexing
            if (m.x+dx >=0) and (m.x+dx < wrld.width()):
                # Loop through delta y
                for dy in [-1, 0, 1]:
                    # Make sure the monster is moving
                    if (dx != 0) or (dy != 0):
                        # Avoid out-of-bound indexing
                        if (m.y+dy >=0) and (m.y+dy < wrld.height()):
                            # No need to check impossible moves
                            if not wrld.wall_at(m.x+dx, m.y+dy):
                                # Set move in wrld
                                pos_Smoves.append([dx, dy])
        return pos_Smoves

    def genSpaceReward(self, wrld, path):
        p = [[0 for _ in range(8)] for _ in range(19)]
        value = 0
        bomb = self.find_bomb(wrld)
        for v in path:
            p[v[1]][v[0]] = value
            neigh = self.get_neighbors_8(wrld, v)
            for n in neigh:
                if p[n[1]][n[0]] == 0:
                    p[n[1]][n[0]] = value
                    neigh2 = self.get_neighbors_8(wrld, n)
                    for n2 in neigh2:
                        if p[n2[1]][n2[0]] == 0:
                            p[n2[1]][n2[0]] = value - 0.1
            value += 1
        
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                if(wrld.exit_at(x, y)): p[y][x] = 500
                elif(wrld.monsters_at(x, y)): p[y][x] = -100
                elif(wrld.explosion_at(x, y)): p[y][x] = -500
                elif(wrld.wall_at(x, y)): 
                    p[y][x] = 0
                
        

        
        if(bomb):
            p[bomb[1]][bomb[0]] = -30
            bomb_object = wrld.bomb_at(bomb[0], bomb[1])
            exp = self.get_explosion_cells(wrld, bomb)
            for e in exp:
                p[e[1]][e[0]] = -5*(6-bomb_object.timer)


        n = []
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                if wrld.monsters_at(x, y):
                    n.append([x, y])

        for q in range(len(n)):
            m = wrld.monsters_at(n[q][0], n[q][1])[0]
            if m:
                p[m.y][m.x] = -100
                mMoves = self.get_pos_moves(m, wrld)
                for move in mMoves:
                    mx = m.x + move[0]
                    my = m.y + move[1]
                    if 0 <= mx and mx < wrld.width() and 0 <= my and my < wrld.height() and p[my][mx] != -100:
                        p[my][mx] = -100

                    mMoves2 = self.get_neighbors_8(wrld, (mx, my))
                    for move2 in mMoves2:
                        mx2 = move2[0]
                        my2 = move2[1]
                        
                        if (0 <= mx2 < wrld.width() and 0 <= my2 < wrld.height()) and p[my2][mx2] not in (-100, -90):
                            p[my2][mx2] = -30

                        mMoves3 = self.get_neighbors_8(wrld, (mx2, my2))
                        for move3 in mMoves3:
                            mx3 = move3[0]
                            my3 = move3[1]

                            if (0 <= mx3 < wrld.width() and 0 <= my3 < wrld.height()) and p[my3][mx3] not in (-100, -90, -80):
                                p[my3][mx3] = -15
                            mMoves4 = self.get_neighbors_8(wrld, (mx3, my3))
                            for move4 in mMoves4:
                                mx4 = move4[0]
                                my4 = move4[1]
    
                                if (0 <= mx4 < wrld.width() and 0 <= my4 < wrld.height()) and p[my4][mx4] not in (-100, -90, -80, -50):
                                    p[my4][mx4] = -12
            monster_path = self.find_monster_path(m, wrld)
            for cell in monster_path:
                p[cell[1]][cell[0]] = -30
            
        return p

    def genPolicy(self, wrld, rewards):
        policy = [[0 for _ in range(8)] for _ in range(19)]
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                possMoves = self.get_neighbors_8(wrld, (x, y))
                if not wrld.wall_at(x, y) and not len(possMoves)==0:
                    bestMove = possMoves[0]
                    bestValue = -float("inf")
                    for move in possMoves:
                        value = rewards[y + move[1]][x + move[0]]
                        if value > bestValue:
                            bestValue = value
                            bestMove = move
                    policy[y][x] = bestMove
        return policy
    
    def genValue(self, wrld,rewards, gamma, policy):
        values = [[0.0 for _ in range(8)] for _ in range(19)]
        for i in range(12):
            new_values = [[0.0 for _ in range(8)] for _ in range(19)]
            for y in range(18):
                for x in range(7):
                    move = policy[y][x]
                    nx = x + move[0]
                    ny = y + move[1]

                    new_values[y][x] = rewards[y][x]+ gamma * values[ny][nx]
            values = new_values

        return values

    def improvPolicy(self, wrld, values):
        new_policy = [[0.0 for _ in range(8)] for _ in range(19)]
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                neigh = self.get_neighbors_8(wrld, (x, y))
                bestMove = [0, 0]
                if neigh:
                    bestMove = [x-neigh[0][0], y-neigh[0][1]]
                    bestValue = -float("inf")
                    for n in neigh:
                        move = [n[0]-x, n[1]-y]
                        val = values[n[1]][n[0]]
                        if val > bestValue:
                            bestValue = val
                            bestMove = move
                new_policy[y][x] = bestMove            
        return new_policy

    def policyIteration(self, wrld, rewards, gamma):
        policy = [[[0, 0] for _ in range(8)] for _ in range(19)]
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                neigh = self.get_neighbors_8(wrld, (x, y))
                possMoves = []
                for n in neigh:
                    possMoves.append([n[0]-x, n[1]-y])
                if len(possMoves)-1 > 0:
                    policy[y][x] = possMoves[random.randint(0, len(possMoves)-1)]

        for i in range(10):
            values = self.genValue(wrld, rewards, gamma, policy)
            new_policy = self.improvPolicy(wrld, values)
            policy = new_policy

        return policy

    def numWalls(self, wrld):
        num = 0
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.wall_at(x, y)): num+=1
        return num

    def get_neighbors_8(self, wrld, cell):
        # List of empty cells
        cells = []

        # Go through neighboring cells
        for nx in [-1, 0, 1]:
            # Avoid out-of-bounds access
            if (
                (cell[0] + nx >= 0)           and
                (cell[0] + nx <  wrld.width())
                ):
                for ny in [-1, 0, 1]:
                    # Avoid out-of-bounds access
                    if (
                        (
                            (cell[1] + ny >= 0)             and
                            (cell[1] + ny <  wrld.height())

                        # Is this cell safe?
                        ) and (
                             wrld.exit_at (cell[0] + nx, cell[1] + ny) or
                             wrld.empty_at(cell[0] + nx, cell[1] + ny)
                        ) and not(
                             wrld.wall_at (cell[0] + nx, cell[1] + ny) or
                             wrld.explosion_at(cell[0] + nx, cell[1] + ny)
                        )
                        ):
                            cells.append((cell[0] + nx, cell[1] + ny))
        return(cells)
    
    def get_neighbors_24(self, wrld, cell):
        # List of empty cells
        cells = []
        # Go through neighboring cells
        for nx in [-2, -1, 0, 1, 2]:
            # Avoid out-of-bounds access
            if (
                (cell[0] + nx >= 0)           and
                (cell[0] + nx <  wrld.width())
                ):
                for ny in [-2, -1, 0, 1, 2]:
                    # Avoid out-of-bounds access
                    if (
                        (
                            (cell[1] + ny >= 0)             and
                            (cell[1] + ny <  wrld.height())

                        # Is this cell safe?
                        ) and (
                                wrld.exit_at (cell[0] + nx, cell[1] + ny) or
                                wrld.empty_at(cell[0] + nx, cell[1] + ny)
                        ) and not(
                             wrld.wall_at (cell[0] + nx, cell[1] + ny) or
                             wrld.explosion_at(cell[0] + nx, cell[1] + ny)
                        )
                        ):
                            cells.append((cell[0] + nx, cell[1] + ny))
        return(cells)

    def euclidean_distance(self, cell_a, cell_b):
        return(
            math.sqrt(
                (cell_a[0] - cell_b[0])**2 + 
                (cell_a[1] - cell_b[1])**2
                )
            )

    def get_edge_cost(self, cell_a, cell_b): return(self.euclidean_distance(cell_a, cell_b))

    def get_heuristic(self, goal, cell):     return(self.euclidean_distance(goal, cell))

    def a_star(self, wrld, start, goal):
        frontier    = PriorityQueue()
        came_from   = {}
        cost_so_far = {}

        

        frontier.put((0, start))
        came_from[start]   = None
        cost_so_far[start] = 0

        while not(frontier.empty()):
            current = frontier.get()[1]

            if(current == goal): break

            for next in self.get_neighbors_8(wrld, current):
                new_cost = cost_so_far[current] + self.get_edge_cost(current, next)

                if(
                    (next not in cost_so_far) or
                    (new_cost < cost_so_far[next])
                    ):
                        cost_so_far[next] = new_cost
                        priority          = new_cost + self.get_heuristic(goal, next)
                        frontier.put((priority, next))
                        came_from[next]   = current

        path = []
        curr_cell = current
        
        while(curr_cell is not None):
            path.append(curr_cell)
            curr_cell = came_from[curr_cell]

        path.reverse()
        return(path)

    def get_world_state(self, wrld):
        character_object = wrld.me(self)
        monster_cells    = set()
        monster_sight_cells    = set()
        bomb_cell        = None
        bomb_timer       = None
        explosion_cells  = set()
        wrld_state       = {}

        for monsters in wrld.monsters.values():
            for monster in monsters:
                monster_cells.add(self.find_monster(wrld))
                for move in self.get_neighbors_24(wrld, self.find_monster(wrld)):
                    monster_sight_cells.add((move[0], move[1]))

        bomb_cell = self.find_bomb(wrld)
        if bomb_cell:
            bomb_object = wrld.bomb_at(bomb_cell[0], bomb_cell[1])
            bomb_timer = bomb_object.timer

        for explosion_cell in wrld.explosions.values():
            explosion_cells.add((explosion_cell.x, explosion_cell.y))

        wrld_state["character cell"]  = None
        if character_object:
            wrld_state["character cell"]  = (character_object.x, character_object.y)
        wrld_state["exit cell"]       = wrld.exitcell
        wrld_state["monster cells"]   = monster_cells
        wrld_state["monster sight cells"]   = monster_sight_cells
        wrld_state["bomb cell"]       = bomb_cell
        wrld_state["bomb timer"]      = bomb_timer
        wrld_state["explosion cells"] = explosion_cells
        wrld_state["explosion range"] = wrld.expl_range

        return(wrld_state)


    def get_dangerous_cells(self, wrld_state, wrld):
        bomb_escape_time       = 5

        bomb_cell              = wrld_state["bomb cell"]
        bomb_time              = wrld_state["bomb timer"]
        explosion_range        = wrld_state["explosion range"]
        monster_sight        = wrld_state["monster sight cells"]
        dangerous_cells        = []

        dangerous_cells.extend(wrld_state["explosion cells"])
        if(bomb_cell): dangerous_cells.append(bomb_cell)

        if(bomb_cell and (bomb_time <= bomb_escape_time)):
            if(bomb_cell and (bomb_time <= bomb_escape_time)):
                dangerous_cells.append(bomb_cell)
                
                for x in range(explosion_range): # Right of bomb                
                    # Add cells only if in world, break otherwise
                    if bomb_cell[0]+x < wrld.width()-1: dangerous_cells.append((bomb_cell[0]+x, bomb_cell[1]))
                    else: break
                    
                    # Add dangerous cell if at wall (explosion lingers in broken wall), then stop
                    if wrld.wall_at(bomb_cell[0] + x, bomb_cell[1]): break
                        
                for x in range(explosion_range): # Left of bomb
                    if bomb_cell[0]-x >= 0: dangerous_cells.append((bomb_cell[0]-x, bomb_cell[1]))
                    else: break
                    
                    if wrld.wall_at(bomb_cell[0] - x, bomb_cell[1]): break
                    
                for y in range(explosion_range): # Below bomb
                    if bomb_cell[1]+y < wrld.height()-1: dangerous_cells.append((bomb_cell[0], bomb_cell[1]+y))
                    else: break
                    
                    if wrld.wall_at(bomb_cell[0], bomb_cell[1]+y): break

                    
                for y in range(explosion_range): # Above bomb
                    if bomb_cell[1]-y >= 0: dangerous_cells.append((bomb_cell[0]-x, bomb_cell[1]-y))
                    else: break
                    
                    if wrld.wall_at(bomb_cell[0], bomb_cell[1]-y): break

        for cell in monster_sight:
            dangerous_cells.append(cell)

        return(dangerous_cells)

    ###
    # wrld         : the world
    # start_cell   : cell to start from
    # blocked_cells: cells to exclude from search
    #
    # >>> returns Look-Up Grid of reachable cell positions and distances from start cell using BFS, excluding given blocked cells
    def lookUpGrid(self, wrld, start_cell, blocked_cells):
        blocked_cells_set = set(blocked_cells)
        blocked_cells_set.discard(start_cell)

        cell_distances = {start_cell: 0}
        frontier = deque([start_cell])

        while frontier:
            current_cell  = frontier.popleft()
            next_distance = cell_distances[current_cell] + 1

            for neighbor in self.get_neighbors_8(wrld, current_cell):
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
        neighbors     = self.get_neighbors_8(wrld, wrld_state["character cell"])
        bomb_ready    = wrld_state["bomb cell"] is None
        legal_actions = []

        for neighbor in neighbors:
            if(neighbor != wrld_state["bomb cell"]):
                legal_actions.append((neighbor, False))
                if(bomb_ready): legal_actions.append((neighbor, True))

        return(legal_actions)


    # >>> returns the hypothetical result of acting out the given action in the current world state as a hypothetical resulting world and its corresponding events
    def do_hypth_action(self, wrld, action):
        (target_cell, place_bomb) = action
        hypth_wrld                = SensedWorld.from_world(wrld)
        hypth_character           = hypth_wrld.me(self)

        hypth_character.move(target_cell[0] - hypth_character.x, target_cell[1] - hypth_character.y)
        if(place_bomb): hypth_character.place_bomb()

        return(hypth_wrld.next())


    def get_reward(self, events, wrld_state):
        reward = -1

        for event in events:
            if  (event.tpe == event.BOMB_HIT_WALL)                   : reward += 5
            elif(event.tpe == event.BOMB_HIT_MONSTER)                : reward += 20
            elif((event.tpe == event.BOMB_HIT_CHARACTER))            : return(-300, True)
            elif((event.tpe == event.CHARACTER_KILLED_BY_MONSTER))   : return(-200, True)
            elif(event.tpe == event.CHARACTER_FOUND_EXIT)            : return(150, True)

        if wrld_state["character cell"]:
            reward = -1/((2*wrld_state["character cell"][1]) + 1)
            if wrld_state["character cell"] in wrld_state["monster sight cells"]:
                reward -= 50

        if wrld_state["monster cells"]:
            reward = -5
            

        return(reward, False)

    ###
    # hypth_wrld: hypothetical / copied world
    #
    # >>> returns feature values given hypothetical world state
    def extract_features(self, hypth_wrld):
        hypth_wrld_state = self.get_world_state(hypth_wrld)
        max_distance     = max(hypth_wrld.width(), hypth_wrld.height()) - 1
        character_cell   = hypth_wrld_state["character cell"]
        exit_cell        = hypth_wrld_state["exit cell"]
        dangerous_cells  = self.get_dangerous_cells(hypth_wrld_state, hypth_wrld)
        lookup_grid      = self.lookUpGrid(hypth_wrld, character_cell, dangerous_cells)
        #num_of_walls     = self.nextToCorner(character_cell, hypth_wrld)
        features         = {}

        features["bias"]                      = 1
        features["exit distance"]             = (min(lookup_grid[exit_cell] / max_distance, 1.0)) if   \
                                                (exit_cell in lookup_grid)                        else \
                                                (min(max(abs(character_cell[0] - exit_cell[0]), abs(character_cell[1] - exit_cell[1])) / max_distance, 1))
        features["monster alive"]                 = (1) if (hypth_wrld_state["monster cells"]) else (0)
        features["nearest monster distance"]  = 1

        for monster_cell in hypth_wrld_state["monster cells"]:
            if((monster_cell in lookup_grid) and ((min(lookup_grid[monster_cell] / max_distance, 1.0)) < features["nearest monster distance"])):
                features["nearest monster distance"] = min(lookup_grid[monster_cell] / max_distance, 1.0)

        features["in danger"]                 = (1) if (hypth_wrld_state["character cell"] in dangerous_cells) else (0)
        #features["next to corners"]                 = num_of_walls
       
        if (features["nearest monster distance"] < self.monsterLastDistance):
            features["monster approching"]  = 1
            print("monster approching: 1")
        else:
            features["monster approching"]  = 0
            print("monster approching: 0")
        

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
               (self.weights["in danger"]                * feature_state["in danger"]               ) +
               (self.weights["monster approching"]       * feature_state["monster approching"]               ) + 
               (self.weights["monster alive"]       *  feature_state["monster alive"])#+ (self.weights["next to corners"]* feature_state["next to corners"])
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
            (reward, done) = self.get_reward(hypth_events, self.get_world_state(hypth_wrld))

            if(done): action_scores.append((action, reward, None, reward))

            else:
                feature_state = self.extract_features(hypth_wrld)
                q_state = self.get_q_state(feature_state)
                action_scores.append((action, q_state, feature_state, reward))

        return(action_scores)

    ###
    # scored_actions: list of scored actions [(action, q-state, features, reward), ...]
    #
    # >>> returns chosen action taking epsilon value into account and breaking best-q-state scored actions randomly
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

            if best_scored_actions:
                chosen_scored_action = random.choice(best_scored_actions)
            else:
                chosen_scored_action = ((0, 0), False), 0.0, None, 0
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
    def update_weights(self, best_next_q_state, done):
        self.prev_q_state = self.get_q_state(self.prev_feature_state)
        delta             = self.prev_reward + ((0) if (done) else (self.gamma * best_next_q_state)) - self.prev_q_state

        self.weights["bias"]                     += self.alpha * delta * self.prev_feature_state["bias"]
        self.weights["exit distance"]            += self.alpha * delta * self.prev_feature_state["exit distance"]
        self.weights["monster alive"]       += self.alpha * delta * self.prev_feature_state["monster alive"]
        self.weights["nearest monster distance"] += self.alpha * delta * self.prev_feature_state["nearest monster distance"]
        self.weights["in danger"]                += self.alpha * delta * self.prev_feature_state["in danger"]
        #self.weights["next to corners"]         += self.alpha * delta * self.prev_feature_state["next to corners"]
        self.weights["monster approching"]       += self.alpha * delta * self.prev_feature_state["monster approching"]
        

    def weights_are_valid(self):

        for value in self.weights.values():
            if math.isnan(value):
                return False
            if math.isinf(value):
                return False
        return True

    def backup_weights(self):
        with open(self.path_to_weights, "r") as file:
            data = json.load(file)

        with open(self.path_to_weightBackups, "w") as file:
            json.dump(data, file, indent=4)

    def restore_weights(self):
        with open(self.path_to_weightBackups, "r") as file:
            data = json.load(file)

        self.epoch = data["epoch"]
        self.weights = data["weights"]

        with open(self.path_to_weights, "w") as file:
            json.dump(data, file, indent=4)

    
    def do(self, wrld):
        exit = self.find_exit(wrld)

        
        goal = exit

        if(self.numWallInRow(3, wrld) < 8):
            self.checkpoint = 0
            goal = (4, 6)

        if(self.numWallInRow(7, wrld) < 8):
            self.checkpoint = 1
            goal = (4, 10)

        if(self.numWallInRow(11, wrld) < 8):
            self.checkpoint = 2
            goal = (4, 14)

        if(self.numWallInRow(15, wrld) < 8):
            self.checkpoint = 3
            goal = exit

        if self.y == goal[1]:
            self.checkpoint += 1

        match self.checkpoint:
            case 0:
                goal = (4, 6)
            case 1:
                goal = (4, 10)
            case 2:
                goal = (4, 14)
            case 3:
                goal = exit


        path = self.a_star(wrld, (self.x, self.y), goal)
        monster = self.find_monster(wrld)
        if monster:
            path2monster = self.a_star(wrld, (self.x, self.y), monster)
        r = self.genSpaceReward(wrld, path)
        for row in range(len(r)):
            print(r[row])

        print(path)
        print(goal)
        
        if path[-1] == goal or (monster and path2monster[-1] == monster and monster[1] >= self.y): 
            p = self.policyIteration(wrld, r, 0.9)
            bestMovement = p[self.y][self.x]
            if(goal == exit and len(path) <= 3):
                bestMovement = [path[1][0] - self.x, path[1][1] - self.y]
            elif((0 <= self.x + bestMovement[1] < wrld.width() and 0 <= self.y + bestMovement[0] < wrld.height()) and r[self.y + bestMovement[0]][self.x + bestMovement[1]] in (-100, -90, -80, -75, -50, -10) and not self.find_bomb(wrld)):
                self.place_bomb()
            print(bestMovement)
            self.move(bestMovement[0], bestMovement[1])
            if bestMovement == [0, 0] and self.find_bomb(wrld) is None:
                self.place_bomb()
                print("Placed bomb")
            else:
                print(bestMovement)
                self.move(bestMovement[0], bestMovement[1])
        else: 
            next_best_q_state = float('-inf')
            
            if(self.weights is None): self.load_weights()

            
            if not(self.weights_are_valid()):
                self.restore_weights()
                    


            wrld_state     = self.get_world_state(wrld)
            legal_actions  = self.get_legal_actions(wrld, wrld_state)
            scored_actions = self.get_action_scores(wrld,legal_actions)

            for scored_action in scored_actions: next_best_q_state = max(next_best_q_state, scored_action[1])

            if(self.prev_feature_state is not None): self.update_weights(next_best_q_state, False)

            if scored_actions:
                chosen_action = self.choose_action(scored_actions)
        
                (the_play, to_bomb_or_not_to_bomb) = chosen_action[0]
                self.prev_feature_state            = chosen_action[2]
                self.prev_reward                   = chosen_action[3]
        
                self.move(the_play[0] - self.x, the_play[1] - self.y)
                if(to_bomb_or_not_to_bomb): self.place_bomb()

            self.save_weights()
            if monster:
                self.monsterLastLocation = monster
                if self.prev_feature_state:
                    self.monsterLastDistance = self.prev_feature_state["nearest monster distance"]

            if self.weights_are_valid():
                self.backup_weights()
        

