# This is necessary to find the main code
import sys
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from colorama import Fore, Back
from math import sqrt
from queue import PriorityQueue

class TestCharacter(CharacterEntity):

    def do(self, wrld):

        char = self.findChar(wrld)
        mstr = self.findMstr(wrld)
        exit = wrld.exitcell

        depth = 4
        distToExpectimax = 10

        self.deathCost = -999
        self.mstrWeight = 100

        distToMstr = len(self.aStar(wrld, char, mstr))

        if (distToMstr < distToExpectimax) :
            next = self.expectimax(wrld, char, mstr, exit, depth)
        else:
            result = self.aStar(wrld, char, exit)
            next = result.pop()
            next = result.pop()


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
    

    # ======== Expectimax ========
    def expectimax(self, wrld, char, mstr, exit, depth):
        # Run expectimax of all surrounding values
        cells = self.getNeighbors8(wrld, char)

        maxVal = float("-inf")
        maxCell = None
        for cell in cells:
            val = self.expectiValue(wrld, cell, mstr, exit, depth)
            print(val)
            val += -len(self.aStar(wrld, cell, exit))
        
            if val > maxVal:
                maxVal = val
                maxCell = cell


        # Return arg max (the state/action responsible for the max value)

        print(maxVal)
        return maxCell

    def expectiValue(self, wrld, char, mstr, exit, depth):
        # If on monster tile, return death cost
        if char == mstr:
            return self.deathCost

        # If at end of depth, return low value to deter overextending
        if depth == 0:
            return -self.euclideanDistance(char, mstr) * self.mstrWeight

        # Set utility value = 0
        val = 0

        # For every action in the state:
        mstrCells = self.getNeighbors8(wrld, mstr)
        p = 1 / len(mstrCells)
        for cell in mstrCells:
            # Calculate probability of hitting monster for each action
            if cell == char:
                val += p * self.deathCost
            else:
                # Value = Value + probability * maxValue(state, action)
                val += p * self.maxValue(wrld, char, cell, exit, depth-1)

        # Return utility value
        return val

    def maxValue(self, wrld, char, mstr, exit, depth):
        # If at exit or max depth, return utility
        if char == exit:
            return 1000
        
        # If at end of depth, return low value to deter overextending
        if depth == 0:
            return -len(self.aStar(wrld, char, mstr)) * self.mstrWeight
        
        # Set utility value to -inf
        val = float("-inf")

        # For every action in the state:
        charCells = self.getNeighbors8(wrld, char)
        for cell in charCells:
            # Value = max(value, expectiValue(state, action))
            val = max(val, self.expectiValue(wrld, cell, mstr, exit, depth-1))

        # Return utility value
        return val


    # ======== Minimax ========
    def minimax(self, wrld, char, mstr, exit, depth):
        # RECURSIVE FUNCTION
        # Returns surrounding cells and values associated with each cell (dict)

        # Calculate monster optimal move
        mstrPath = self.aStar(wrld, mstr, char)
        next = mstrPath.pop()
        next = mstrPath.pop()

        (mx, my) = mstr
        (nx, ny) = next
        (x, y) = (nx-mx, ny-my)
        mstr = (mstr[0]+x, mstr[1]+y)

        # Locate surrounding cells
        charCells = self.getNeighbors8(wrld, char)
        mstrCells = self.getNeighbors8(wrld, mstr)
        mstrCells.append(mstr)

        # Cull cells that are shared with the monster and the cells surrounding the monster
        temp = []
        for cell in charCells:
            if cell not in mstrCells:
                temp.append(cell)
            
        cells = temp

        # If depth is 0, return score of each surrounding cell
        if depth == 0:
            scores = []

            for cell in cells:
                score = len(self.aStar(wrld, cell, exit))
                scores.append((cell, score))

            return scores

        # Recursively call function
        depth -= 1
        results = []
        for cell in cells:
            results.append(self.minimax(wrld, cell, mstr, exit, depth))

        # If returned a set of cells and values, return the cell with the highest value
        minVal = 999
        minCell = None
        for set in results:
            for cell in set:
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