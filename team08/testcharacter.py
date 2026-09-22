# This is necessary to find the main code
import sys
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from colorama import Fore, Back
from math import sqrt
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

        minimaxDepth = 10
        minimaxEnableDist = 4

        charMstrDist = len(self.aStar(wrld, char, mstr)) - 1

        if charMstrDist < minimaxEnableDist:
            print("MINIMAX")

            result = self.minimax(wrld, char, mstr, exit, minimaxDepth)
            next = result[0]

            print("Next", next)

        else:
            print("A*")

            path = self.aStar(wrld, char, exit)
            next = path.pop()
            next = path.pop()


        (cx, cy) = char
        (nx, ny) = next
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


    # ======== Minimax ========
    def minimax(self, wrld, char, mstr, exit, depth):
        # RECURSIVE FUNCTION
        # Returns surrounding cells and values associated with each cell (dict)

        # Calculate monster optimal move
        cells = self.getNeighbors8(wrld, mstr)

        minVal = 999.0
        minCell = None
        for cell in cells:
            dist = self.euclideanDistance(cell, char)

            if dist < minVal:
                minVal = dist
                minCell = cell

        (mx, my) = mstr
        (nx, ny) = minCell
        (x, y) = (nx-mx, ny-my)

        mstr = (mstr[0]+x, mstr[1]+y)

        # Locate surrounding cells
        cells = self.getNeighbors8(wrld, char)

        # Cull cells that are share with the monster
        temp = []
        for cell in cells:
            if cell != mstr:
                temp.append(cell)

        cells = temp

        # If depth is 0, return score of each surrounding cell
        if depth == 0:
            scores = []

            for cell in cells:
                score = self.aStar(wrld, cell, exit)
                scores.append((cell, score))

            print(scores)

            return cells

        # Recursively call function
        depth -= 1
        result = self.minimax(wrld, char, mstr, exit, depth)

        # If returned a set of cells and values, return the cell with the highest value
        minVal = 999
        minCell = None
        for cell in result:
            if cell[1] < minVal:
                minVal = cell[1]
                minCell = cell[0]

        return [(minCell, minVal)]


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