# This is necessary to find the main code
import math
from math import sqrt
import sys
from queue import PriorityQueue
import random
import numpy as np
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from colorama import Fore, Back


class TestCharacter(CharacterEntity):

    variant = 0

    def setVariant(self, variant):
        self.variant = variant

    def getVariant(self):
        return self.variant
    
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

    def find_bomb(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.bomb_at(x, y)): return((x, y))

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

    def get_pos_moves(self, m, wrld):
        pos_Smoves = [[0,0]]
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

    def a_star(self, wrld):
        frontier    = PriorityQueue()
        came_from   = {}
        cost_so_far = {}

        start = (self.x, self.y)
        goal  = self.find_exit(wrld)

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

    def genSpaceReward3(self, wrld, path):
        p = [[0 for _ in range(8)] for _ in range(19)]
        value = 0
        for v in path:
            p[v[1]][v[0]] = value
            neigh = self.get_neighbors_8(wrld, v)
            for n in neigh:
                if p[n[1]][n[0]] == 0:
                    p[n[1]][n[0]] = value - 0.1
                    neigh2 = self.get_neighbors_8(wrld, n)
                    for n2 in neigh2:
                        if p[n2[1]][n2[0]] == 0:
                            p[n2[1]][n2[0]] = value - 0.2
            value += 1
        print(path)
        
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                if(wrld.exit_at(x, y)): p[y][x] = 500
                elif(wrld.monsters_at(x, y)): p[y][x] = -100
                elif(wrld.explosion_at(x, y)): p[y][x] = -50
                elif(wrld.wall_at(x, y)): 
                    p[y][x] = 0
                
        

        bomb = self.find_bomb(wrld)
        if(bomb):
            p[bomb[1]][bomb[0]] -= 20
            for y in range(wrld.height()):
                for x in range(wrld.width()):
                    not wrld.wall_at(x, y)
                    if not wrld.wall_at(x, y) and (x == bomb[0] or y == bomb[1]):
                        p[y][x] -= 2

        n = self.find_monster(wrld)
        m = wrld.monsters_at(n[0], n[1])[0]
        p[m.y][m.x] = -100
        mMoves = self.get_pos_moves(m, wrld)
        for move in mMoves:
            mx = m.x + move[0]
            my = m.y + move[1]
            if 0 <= mx and mx < wrld.width() and 0 <= my and my < wrld.height() and p[my][mx] != -100:
                p[my][mx] = -75

            mMoves2 = self.get_neighbors_8(wrld, (mx, my))
            for move2 in mMoves2:
                mx2 = move2[0]
                my2 = move2[1]
                
                if (0 <= mx2 < wrld.width() and 0 <= my2 < wrld.height()) and p[my2][mx2] not in (-100, -75):
                    p[my2][mx2] = -20

                mMoves3 = self.get_neighbors_8(wrld, (mx2, my2))
                for move3 in mMoves3:
                    mx3 = move3[0]
                    my3 = move3[1]

                    if (0 <= mx3 < wrld.width() and 0 <= my3 < wrld.height()) and p[my3][mx3] not in (-100, -75, -20):
                        p[my3][mx3] = -5
            
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
                    if not isinstance(move, float):
                        nx = x + move[0]
                        ny = y + move[1]

                        new_values[y][x] = rewards[y][x]+ gamma * values[ny][nx]
            values = new_values

        return values

    def improvPolicy(self, wrld, values):
        bestMove = [0, 0]
        new_policy = [[0.0 for _ in range(8)] for _ in range(19)]
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                neigh = self.get_neighbors_8(wrld, (x, y))
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

    def genSpaceReward5(self, wrld, path):
        p = [[0 for _ in range(8)] for _ in range(19)]
        value = 0
        bomb = self.find_bomb(wrld)
        if not bomb:
            for v in path:
                p[v[1]][v[0]] = value
                neigh = self.get_neighbors_8(wrld, v)
                for n in neigh:
                    if p[n[1]][n[0]] == 0:
                        p[n[1]][n[0]] = value - 0.1
                        neigh2 = self.get_neighbors_8(wrld, n)
                        for n2 in neigh2:
                            if p[n2[1]][n2[0]] == 0:
                                p[n2[1]][n2[0]] = value - 0.2
                value += 1
            print(path)
        
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                if(wrld.exit_at(x, y)): p[y][x] = 500
                elif(wrld.monsters_at(x, y)): p[y][x] = -100
                elif(wrld.explosion_at(x, y)): p[y][x] = -500
                elif(wrld.wall_at(x, y)): 
                    p[y][x] = 0
                
        

        
        if(bomb):
            p[bomb[1]][bomb[0]] = -30
            exp = self.get_explosion_cells(wrld, bomb)
            for e in exp:
                p[e[1]][e[0]] = -10


        n = []
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                if wrld.monsters_at(x, y):
                    n.append([x, y])

        for q in range(len(n)):
            m = wrld.monsters_at(n[q][0], n[q][1])[0]
            if m.name == "stupid":
                p[m.y][m.x] = -100
                mMoves = self.get_pos_moves(m, wrld)
                for move in mMoves:
                    mx = m.x + move[0]
                    my = m.y + move[1]
                    if 0 <= mx and mx < wrld.width() and 0 <= my and my < wrld.height() and p[my][mx] != -100:
                        p[my][mx] = -75
                    mMoves2 = self.get_neighbors_8(wrld, (mx, my))
                    for move2 in mMoves2:
                        mx2 = move2[0]
                        my2 = move2[1]
                        if (0 <= mx2 < wrld.width() and 0 <= my2 < wrld.height()) and p[my2][mx2] not in (-100, -75):
                            p[my2][mx2] = -50
            else:
                p[m.y][m.x] = -100
                mMoves = self.get_pos_moves(m, wrld)
                for move in mMoves:
                    mx = m.x + move[0]
                    my = m.y + move[1]
                    if 0 <= mx and mx < wrld.width() and 0 <= my and my < wrld.height() and p[my][mx] != -100:
                        p[my][mx] = -90

                    mMoves2 = self.get_neighbors_8(wrld, (mx, my))
                    for move2 in mMoves2:
                        mx2 = move2[0]
                        my2 = move2[1]
                        
                        if (0 <= mx2 < wrld.width() and 0 <= my2 < wrld.height()) and p[my2][mx2] not in (-100, -90):
                            p[my2][mx2] = -80

                        mMoves3 = self.get_neighbors_8(wrld, (mx2, my2))
                        for move3 in mMoves3:
                            mx3 = move3[0]
                            my3 = move3[1]

                            if (0 <= mx3 < wrld.width() and 0 <= my3 < wrld.height()) and p[my3][mx3] not in (-100, -90, -80):
                                p[my3][mx3] = -50
                            mMoves4 = self.get_neighbors_8(wrld, (mx3, my3))
                            for move4 in mMoves4:
                                mx4 = move4[0]
                                my4 = move4[1]
    
                                if (0 <= mx4 < wrld.width() and 0 <= my4 < wrld.height()) and p[my4][mx4] not in (-100, -90, -80, -50):
                                    p[my4][mx4] = -10
            
        return p

    def policyIteration3(self, wrld, rewards, gamma):
        policy = [[0.0 for _ in range(8)] for _ in range(19)]
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                neigh = self.get_neighbors_8(wrld, (x, y))
                possMoves = []
                for n in neigh:
                    possMoves.append([n[0]-x, n[1]-y])

                policy[y][x] = possMoves[random.randint(0, len(possMoves)-1)]

        for i in range(10):
            values = self.genValue(wrld, rewards, gamma, policy)
            new_policy = self.improvPolicy(wrld, values)
            policy = new_policy

        return policy

    def policyIteration5(self, wrld, rewards, gamma):
        policy = [[0.0 for _ in range(8)] for _ in range(19)]
        for y in range(wrld.height()):
            for x in range(wrld.width()):
                neigh = self.get_neighbors_8(wrld, (x, y))
                possMoves = []
                for n in neigh:
                    possMoves.append([n[0]-x, n[1]-y])

                if possMoves:
                    policy[y][x] = possMoves[random.randint(0, len(possMoves)-1)]
                else:
                    policy[y][x] = [0, 0]

        for i in range(10):
            values = self.genValue(wrld, rewards, gamma, policy)
            new_policy = self.improvPolicy(wrld, values)
            policy = new_policy

        return policy

    # max depth/amount of tree layers to explore (full turns)
    search_depth = 3

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

    ##
    # exit          {absolute}(x, y): exit cell
    # character_pos {absolute}(x, y): given character position
    # monster_pos   {absolute}(x, y): given monster position
    # depth                   [int] : current search depth
    #
    # >>> returns whether the search is at a terminal state and should end
    def terminal(self, exit, character_pos, monster_pos, depth):
        return(
            (character_pos == exit)              or
            (character_pos == monster_pos)       or
            (depth         >= self.search_depth)
            )

    ##
    # exit          {absolute}(x, y): exit cell
    # character_pos {absolute}(x, y): given character position
    # monster_pos   {absolute}(x, y): given monster position
    # depth                   [int] : current search depth
    #
    # >>> returns node utility
    def utility(self, exit, character_pos, monster_pos, depth):
        # getting to the exit sooner is better
        if(character_pos == exit)       : return( 100 - depth)
        # dying is bad
        if(character_pos == monster_pos): return(-100)

        # ratio of exit approach vs. monster avoidance
        k = 1.0

        # over max search depth
        if(depth         >= self.search_depth):
            exit_dist    = self.euclidean_distance(character_pos, exit)
            monster_dist = self.euclidean_distance(character_pos, monster_pos)

            return(-(k * exit_dist) + ((1 - k) * monster_dist))

    ##
    # wrld                  [SensedWorld]: given world state
    # monster_pos {absolute}(x, y)       : given monster position
    # action      {absolute}(x, y)       : given action
    # who                   [boolean]    : whom to move {True -> Character, False -> Monster}
    #
    # >>> moves corresponding agent in hypothetical world, returns said world, new character position, and new monster position
    def result(self, wrld, monster_pos, action, who):
        hypth_wrld    = wrld.from_world(wrld)
        character     = hypth_wrld.me(self)
        character_pos = (character.x, character.y)
        monster       = hypth_wrld.monsters_at(monster_pos[0], monster_pos[1])[0]

        # move character
        if(who):
            character.move(action[0] - character_pos[0], action[1] - character_pos[1])
            hypth_wrld.update_character_move(character, True)
            new_character_pos = (character.x, character.y)
            new_monster_pos   = monster_pos

        # move monster
        else   :
            monster.move(  action[0] - monster_pos[0]  , action[1] - monster_pos[1])
            hypth_wrld.update_monster_move(monster, True)
            new_character_pos = character_pos
            new_monster_pos   = (monster.x, monster.y)

        return(hypth_wrld, new_character_pos, new_monster_pos)

    ##
    # wrld                       [SensedWorld]: given world state
    # exit             {absolute}(x, y)       : exit cell
    # character_pos    {absolute}(x, y)       : given character position
    # monster_pos      {absolute}(x, y)       : given monster position
    # doing_expectimax          [boolean]     : whether to recurse with a min (minimax) or chance (expectimax) node next
    # depth                     [int]         : current search depth
    #
    # >>> returns found node utility
    def max_node(self, wrld, exit, character_pos, monster_pos, doing_expectimax, depth):
        # get utility if terminal
        if(self.terminal(exit, character_pos, monster_pos, depth)):
            return(self.utility(exit, character_pos, monster_pos, depth))

        # start off with $-\infty$
        val = float("-inf")

        # consider character moves
        for action in self.get_neighbors_8(wrld, character_pos):
            (hypth_wrld, new_character_pos, new_monster_pos) = self.result(wrld, monster_pos, action, True)

            # call chance node if running expectimax, min node if running minimax
            if(doing_expectimax): val = max(val, self.chance_node(hypth_wrld, exit, new_character_pos, new_monster_pos, depth + 1))
            else                : val = max(val, self.min_node(hypth_wrld, exit, new_character_pos, new_monster_pos, depth + 1))

        return(val)

    ##
    # wrld                       [SensedWorld]: given world state
    # exit             {absolute}(x, y)       : exit cell
    # character_pos    {absolute}(x, y)       : given character position
    # monster_pos      {absolute}(x, y)       : given monster position
    # depth                      [int]        : current search depth
    #
    # >>> returns found node utility
    def min_node(self, wrld, exit, character_pos, monster_pos, depth):
        # get utility if terminal
        if(self.terminal(exit, character_pos, monster_pos, depth)):
            return(self.utility(exit, character_pos, monster_pos, depth))

        # start off with $\infty$
        val = float("inf")

        # consider monster moves
        for action in self.get_neighbors_8(wrld, monster_pos):
            (hypth_wrld, new_character_pos, new_monster_pos) = self.result(wrld, monster_pos, action, False)
            val                                              = min(val, self.max_node(hypth_wrld, exit, new_character_pos, new_monster_pos, False, depth))

        return(val)

    ##
    # wrld                       [SensedWorld]: given world state
    # exit             {absolute}(x, y)       : exit cell
    # character_pos    {absolute}(x, y)       : given character position
    # monster_pos      {absolute}(x, y)       : given monster position
    # depth                      [int]        : current search depth
    #
    # >>> returns found node utility
    def chance_node(self, wrld, exit, character_pos, monster_pos, depth):
        # get utility if terminal
        if(self.terminal(exit, character_pos, monster_pos, depth)):
            return(self.utility(exit, character_pos, monster_pos, depth))

        # get monster moves
        monster_actions = self.get_neighbors_8(wrld, monster_pos)
        # start off with zero
        val             = 0
        # get probability from actions (all equally likely for monster wandering, whether stupid or not)
        prob            = 1.0 / len(monster_actions)

        # consider monster moves
        for action in monster_actions:
            (hypth_wrld, new_character_pos, new_monster_pos)  = self.result(wrld, monster_pos, action, False)
            val                                              += prob * self.max_node(hypth_wrld, exit, new_character_pos, new_monster_pos, True, depth)

        return(val)

    ##
    # wrld [SensedWorld]: sensed world state
    #
    # >>> returns best action to take
    def root_node(self, wrld):
        exit          = wrld.exitcell
        character_pos = (self.x, self.y)
        monsters      = self.find_monsters(wrld)
        actions       = self.get_neighbors_8(wrld, character_pos)
        dists         = []
        vals          = []

        # get closest monster and distance to it
        for monster in monsters: dists.append(self.euclidean_distance(character_pos, monster))
        dist_to_monster = min(dists)
        monster_pos     = monsters[np.argmin(dists)]

        # consider character actions
        for action in actions:
            (hypth_wrld, new_character_pos, new_monster_pos) = self.result(wrld, monster_pos, action, True)

            # run expectimax if far enough away from the closest monster, minimax otherwise
            if(dist_to_monster < 2.83): vals.append(self.min_node(hypth_wrld, exit, new_character_pos, new_monster_pos, 1))
            else                      : vals.append(self.chance_node(hypth_wrld, exit, new_character_pos, new_monster_pos, 1))

        best_action = actions[np.argmax(vals)]
            
        return(best_action[0] - character_pos[0], best_action[1] - character_pos[1])

    def evaluatePose(self, wrld, char, mstr, exit):
        
        # Calculate score of a state given character distance to monster and exit
        mstrDist = self.euclideanDistance(char, mstr)
        
        score = 0
        score += mstrDist * self.mstrWeight
        score -= len(self.aStar(wrld, char, exit)) * self.exitWeight
        
        # Only add this score if the monster will start deterministically chasing
        if mstrDist < self.mstrChaseDist:
            score -= 1 / mstrDist * self.mstrChaseCost
        
        return score

    def findChar(self, wrld):
        return wrld.me(self).x, wrld.me(self).y

    def findMstr(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if wrld.monsters_at(x, y):
                    return (x, y)

        return None

    def mstrAtWall(self, wrld, mstr):
                
        # Define position after next move
        x = mstr[0] + self.mstrMovement[0]*2
        y = mstr[1] + self.mstrMovement[1]*2        
        
        # Check if next move is in a wall or barrier
        width = wrld.width()
        height = wrld.height()
        
        # Check if next cell is a barrier
        if (x<0 or x>width-1) or (y<0 or y>height-1) or wrld.wall_at(x, y):
            return True
        
        return False

    # ======== Expectimax ========
    def expectimax(self, wrld, char, mstr, exit, depth):
        
        # Run expectimax of all surrounding values
        cells = self.getNeighbors8(wrld, char)

        maxVal = float("-inf")
        maxCell = None
        for cell in cells:
            val = self.expValue(wrld, cell, mstr, exit, depth)
            val += -len(self.aStar(wrld, cell, exit))
                    
            if val > maxVal:
                maxVal = val
                maxCell = cell

        # Return arg max (the state/action responsible for the max value)
        return maxCell

    def expValue(self, wrld, char, mstr, exit, depth):
        
        # If on monster tile, return death cost
        if char == mstr:
            return self.deathCost

        # If at end of depth, return low value to deter overextending
        if depth == 0:
            return self.evaluatePose(wrld, char, mstr, exit)

        # Set utility value = 0
        val = 0

        # If within monster chasse distance, monster moves deterministically
        if self.euclideanDistance(char, mstr) <= self.mstrChaseDist:
            
            # Calculate ideal monster move
            x = char[0] - mstr[0]
            y = char[1] - mstr[1]
            
            # Clamp movement
            x = max(-1, min(x, 1))
            y = max(-1, min(x, 1))
            
            next = (mstr[0]+x, mstr[1]+y)
            
            if next == char:
                val += self.deathCost
            else:
                # Value = Value + probability * maxValue(state, action)
                val += self.expectiMaxValue(wrld, char, next, exit, depth-1)
                
                # Subtract from score if monster is chasing
                val -= self.mstrChaseCost
        
        # If at wall, monster moves randomly in direction with probability of 1/(possible moves)
        elif self.mstrAtWall(wrld, mstr):
            
            # For every action in the state:
            mstrCells = self.getNeighbors8(wrld, mstr)
            p = 1 / len(mstrCells)
            for cell in mstrCells:
                # Calculate probability of hitting monster for each action
                if cell == char:
                    val += p * self.deathCost
                else:
                    # Value = Value + probability * maxValue(state, action)
                    val += p * self.expectiMaxValue(wrld, char, cell, exit, depth-1)
                    
        # If outside two cells, monster moves deterministically
        else:
                        
            # Calculate next monster move
            x = mstr[0] + self.mstrMovement[0]
            y = mstr[1] + self.mstrMovement[1]
                        
            next = (x, y)
            
            if next == char:
                val += self.deathCost
            else:
                # Value = Value + probability * maxValue(state, action)
                val += self.expectiMaxValue(wrld, char, next, exit, depth-1) 

        # Return utility value
        return val

    def expectiMaxValue(self, wrld, char, mstr, exit, depth):
        
        # If at exit or max depth, return utility
        if char == exit:
            return 1000
        
        # If at end of depth, return low value to deter overextending
        if depth == 0:
            return self.evaluatePose(wrld, char, mstr, exit)
        
        # Set utility value to -inf
        val = float("-inf")

        # For every action in the state:
        charCells = self.getNeighbors8(wrld, char)
        for cell in charCells:
            # Value = max(value, expectiValue(state, action))
            val = max(val, self.expValue(wrld, cell, mstr, exit, depth-1))

        # Return utility value
        return val

    # ======== A* Calculations ========

    def getNeighbors8(self, wrld, cell):

        width = wrld.width()
        height = wrld.height()

        # Empty list to store cells
        cells = []

        # Go through neighboring cells in x-direction
        for nx in [-1, 0, 1]:
            x = cell[0] + nx

            # Avoid out-of-bounds access
            if x < 0 or x > width-1: continue

            # Go through neighboring cells in y-direction
            for ny in [-1, 0, 1]:
                y = cell[1] + ny

                # Skip (0, 0)
                if nx == 0 and ny == 0: continue

                # Avoid out-of-bounds access
                if y < 0 or y > height-1: continue

                # Check if cell is safe
                if wrld.exit_at(x, y) or wrld.empty_at(x, y) or wrld.characters_at(x, y) or wrld.monsters_at(x, y):

                    # Add cell to cell list
                    cells.append((x, y))
                    
        return cells

    def euclideanDistance(self, a, b):
        return sqrt( (a[0] - b[0])**2 + (a[1] - b[1])**2 )

    def aStar(self, wrld, start, goal):

        # Define A* variables
        frontier    = PriorityQueue()
        came_from   = {}
        cost_so_far = {}

        # Set start node
        frontier.put((0, start))
        came_from[start]   = None
        cost_so_far[start] = 0

        while not frontier.empty():

            # Remove highest prioririty item from frontier
            current = frontier.get()[1]

            # Exit loop if at goal
            if current == goal: break

            # Check neighbors of current node
            for next in self.getNeighbors8(wrld, current):

                # Calculate move cost to next node
                new_cost = cost_so_far[current] + self.euclideanDistance(current, next)

                # If next wasn't visited or the path to next is cheaper than the existing:
                if (next not in cost_so_far) or (new_cost < cost_so_far[next]):

                    # Set cost, calculate heuristic, and store in queue
                    cost_so_far[next] = new_cost
                    priority          = new_cost + self.euclideanDistance(goal, next)
                    frontier.put((priority, next))
                    came_from[next]   = current

        # Fill path
        path = []

        while current is not None:

            # Backtrack from current node to get to original
            path.append(current)
            current = came_from[current]

        return path



    
    def do(self, wrld):
        # Your code here

        if self.getVariant() == 1:
            path = self.a_star(wrld)

            if(len(path) <= 1): return

            self.move(path[1][0] - self.x, path[1][1] - self.y)

        elif self.getVariant() == 2:
            the_play = self.root_node(wrld)
            self.move(the_play[0], the_play[1])

        elif self.getVariant() == 3:
            path = self.a_star(wrld)
            r = self.genSpaceReward3(wrld, path)

            p = self.policyIteration3(wrld, r, 0.9)

            bestMovement = p[self.y][self.x]
            if(len(path) <= 5):
                bestMovement = [path[1][0] - self.x, path[1][1] - self.y]
            print(bestMovement)
            self.move(bestMovement[0], bestMovement[1])

        elif self.getVariant() == 4:
            # Locate entities and exit coordinates
            char = self.findChar(wrld)
            mstr = self.findMstr(wrld)
            exit = wrld.exitcell
            
            # Determine which direction the monster is moving in
            m = next(iter(wrld.monsters.values()))
            self.mstrMovement = (m[0].dx, m[0].dy)
            
            # Define expectimax start and depth variables
            depth = 4
            mstrDist = 6

            # Define weights for expectimax states and actions
            self.deathCost = -999
            self.mstrWeight = 10
            self.exitWeight = 10
            self.mstrChaseDist = 2.8
            self.mstrChaseCost = 100

            # Use A* or expectimax depending on monster proximity
            distToMstr = len(self.aStar(wrld, char, mstr))
            
            if distToMstr < mstrDist:
                nextStep = self.expectimax(wrld, char, mstr, exit, depth)

            else:
                result = self.aStar(wrld, char, exit)
                nextStep = result.pop()
                nextStep = result.pop()

            # Execute best move
            (cx, cy) = char
            (nx, ny) = nextStep
            (x, y) = (nx-cx, ny-cy)
            self.move(x, y)

        elif self.getVariant() == 5:
            path = self.a_star(wrld)
            r = self.genSpaceReward5(wrld, path)

            p = self.policyIteration5(wrld, r, 0.9)

            n = []
            for y in range(wrld.height()):
                for x in range(wrld.width()):
                    if wrld.monsters_at(x, y):
                        n.append([x, y])

            away_from_stupid = 0
            away_from_agress = 0
            monster_count = 0
            for q in range(len(n)):
                monster_count += 1
                m = wrld.monsters_at(n[q][0], n[q][1])[0]
                if m.name == "stupid":
                    away_from_stupid = self.euclidean_distance([self.x, self.y], [n[q][0], n[q][1]])
                else:
                    away_from_agress = self.euclidean_distance([self.x, self.y], [n[q][0], n[q][1]])
            
            bestMovement = p[self.y][self.x]
            print("Chosen Policy: " + str(bestMovement))
            if(len(path) <= 3):
                bestMovement = [path[1][0] - self.x, path[1][1] - self.y]
            elif((0 <= self.x + bestMovement[1] < wrld.width() and 0 <= self.y + bestMovement[0] < wrld.height()) and r[self.y + bestMovement[0]][self.x + bestMovement[1]] in (-100, -90, -80, -75, -50, -10) and not self.find_bomb(wrld)):
                self.place_bomb()
            print(bestMovement)
            self.move(bestMovement[0], bestMovement[1])


    