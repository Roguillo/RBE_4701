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

        minimaxDepth = 6
        expectimaxDepth = 4

        # Use these values for hysterises when switching states
        closeVal = 4
        farVal = 6

        self.deathCost = -999
        self.mstrWeight = 20
        self.exitWeight = 1

        distToMstr = len(self.aStar(wrld, char, mstr))

        state = "A*"
        print("Distance:", distToMstr)

        if distToMstr <= closeVal:
            next = self.minimax(wrld, char, mstr, exit, minimaxDepth)
            state = "mini"
            print("Test")

        elif distToMstr <= farVal:
            next = self.expectimax(wrld, char, mstr, exit, expectimaxDepth)
            state = "expecti"

        else:
            result = self.aStar(wrld, char, exit)
            next = result.pop()
            next = result.pop()
            state = "A*"

        print("State:", state)

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
            return self.euclideanDistance(char, mstr) * self.mstrWeight - self.euclideanDistance(char, exit) * self.exitWeight

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
                val += p * self.expectiMaxValue(wrld, char, cell, exit, depth-1)

        # Return utility value
        return val

    def expectiMaxValue(self, wrld, char, mstr, exit, depth):
        # If at exit or max depth, return utility
        if char == exit:
            return 1000
        
        # If at end of depth, return low value to deter overextending
        if depth == 0:
            return self.euclideanDistance(char, mstr) * self.mstrWeight - self.euclideanDistance(char, exit) * self.exitWeight
        
        # Set utility value to -inf
        val = float("-inf")

        # For every action in the state:
        charCells = self.getNeighbors8(wrld, char)
        for cell in charCells:
            # Value = max(value, expectiValue(state, action))
            val = max(val, self.expValue(wrld, cell, mstr, exit, depth-1))

        # Return utility value
        return val


    # ======== Minimax ========
    def minimax(self, wrld, char, mstr, exit, depth):
        # Run minimax of all surrounding values
        cells = self.getNeighbors8(wrld, char)

        maxVal = float("-inf")
        maxCell = None
        for cell in cells:
            val = self.minValue(wrld, cell, mstr, exit, depth)
  
            if val > maxVal:
                maxVal = val
                maxCell = cell


        # Return arg max (the state/action responsible for the max value)
        return maxCell

    def minValue(self, wrld, char, mstr, exit, depth):
        # If on monster tile, return death cost
        if char == mstr:
            return self.deathCost

        # If at end of depth, return low value to deter overextending
        if depth == 0:
            return self.euclideanDistance(char, mstr) * self.mstrWeight - self.euclideanDistance(char, exit) * self.exitWeight

        # Set utility value = inf
        val = float("inf")

        # For every action in the state:
        mstrCells = self.getNeighbors8(wrld, mstr)
        for cell in mstrCells:
            # Value = min(value, maxValueMini(state, action))
            val = min(val, self.maxValue(wrld, char, cell, exit, depth-1))

        # Return utility value
        return val

    def maxValue(self, wrld, char, mstr, exit, depth):
        # If at exit or max depth, return utility
        if char == exit:
            return 1000
        
        # If at end of depth, return low value to deter overextending
        if depth == 0:
            return self.euclideanDistance(char, mstr) * self.mstrWeight - self.euclideanDistance(char, exit) * self.exitWeight
        
        # Set utility value to -inf
        val = float("-inf")

        # For every action in the state:
        charCells = self.getNeighbors8(wrld, char)
        for cell in charCells:
            # Value = max(value, maxiValue(state, action))
            val = max(val, self.minValue(wrld, cell, mstr, exit, depth-1))

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