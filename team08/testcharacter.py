# This is necessary to find the main code
import sys
import math
import random
from queue import PriorityQueue
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from colorama import Fore, Back

class TestCharacter(CharacterEntity):

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

    def genSpaceReward(self, wrld, path):
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


        m = next(iter(wrld.monsters.values()))[0]
        p[m.y][m.x] = -100
        mMoves = self.get_pos_moves(m, wrld)
        for move in mMoves:
            mx = m.x + move[0]
            my = m.y + move[1]
            if 0 <= mx and mx < wrld.width() and 0 <= my and my < wrld.height():
                p[my][mx] = -100
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


    
    def do(self, wrld):
        # Your code here
        exit = self.find_exit(wrld)
        path = self.a_star(wrld, (self.x, self.y), exit)
        r = self.genSpaceReward(wrld, path)
        for l in r:
            print(l)

        p = self.policyIteration(wrld, r, 0.9)

        bestMovement = p[self.y][self.x]
        if(len(path) <= 5):
            bestMovement = [path[1][0] - self.x, path[1][1] - self.y]
        print(bestMovement)
        self.move(bestMovement[0], bestMovement[1])


    