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