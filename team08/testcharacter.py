# This is necessary to find the main code
import sys
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from colorama import Fore, Back
import math
from queue import PriorityQueue

class TestCharacter(CharacterEntity):

    """
    This solution uses a combination of A* path planning and expectimax.

    A* will be used to get values for each tile to prioritize exiting.

    Expectimax will be able to handle both deterministic monster
    paths (moving straight or within two blocks range of character)
    and random aspects (random direction moving from wall).

    Only a few levels of expectimax will be calculated to save on
    both time and space complexity
    """

    def do(self, wrld):

        char = self.findChar(wrld)
        mstr = self.findMstr(wrld)
        exit = wrld.exitcell

        targetMstrDist = 3
        mstrDistWeight = 5

        # Iterate through eight cells surrounding player
        # Give each cell a score as a sum of dist to goal
        # and distance to monster
        cells = self.get_neighbors_8(wrld, char)
        minScore = 999
        bestMove = None
        for cell in cells:
            score = len(self.a_star(wrld, cell, exit))

            cellMstrDist = self.distToMonster(wrld, cell, mstr)

            if cellMstrDist <= targetMstrDist:
                score += (targetMstrDist - cellMstrDist + 1) * mstrDistWeight

            if score < minScore:
                minScore = score
                bestMove = cell



        # path = self.a_star(wrld, char, exit)
        # exitDist = len(path)

        # next = path.pop()
        # next = path.pop()

        (cx, cy) = char
        (nx, ny) = bestMove
        (x, y) = (nx-cx, ny-cy)
        self.move(x, y)


    def findChar(self, wrld):
        return (wrld.me(self).x, wrld.me(self).y)

    def findMstr(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if wrld.monsters_at(x, y):
                    return (x, y)

        return None

    def findExit(self, wrld):
            for x in range(wrld.width()):
                for y in range(wrld.height()):
                    if wrld.exit_at(x, y):
                        return (x, y)
    
            return None
    
    def monsterWall(wrld, mstr, prevMstr):
        # If monster is moving in a direction and a wall, barrier, or map corner is in the way, return true
        dir = prevMstr - mstr
        next = mstr + dir
        char = wrld[next[0], next[1]]

        if char == "W" or char == "|" or char == "+" or char == "-":
            return True
        
        return False

    def distToMonster(self, wrld, char, mstr):
        return len(self.a_star(wrld, char, mstr))


    # ======== A* Calculations ========

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

        # path.reverse()
        return(path)