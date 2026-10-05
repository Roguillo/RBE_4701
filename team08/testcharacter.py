# This is necessary to find the main code
import sys
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from colorama import Fore, Back
from math import sqrt
from queue import PriorityQueue
import numpy as np
import os

class TestCharacter(CharacterEntity):

    def do(self, wrld):

        # File management for reading/storing weights
        # Found at https://www.geeksforgeeks.org/python/reading-writing-text-files-python/
        # File pathing found at https://www.tutorialspoint.com/article/how-to-open-a-file-in-the-same-directory-as-a-python-script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'weights.txt')
        f1 = open(file_path, "r") # Read

        # Store weights in wfs array
        wfs = []
        line = f1.readline()
        while line is not "":
            wfs.append((float(line), None))
            line = f1.readline()

        # Define reward values
        self.liveReward = 0
        self.exitReward = 100
        self.deathReward = -999
        self.costOfLiving = -1
        self.discount = 0.95
        self.learnRate = 0.01


        
    # TODO: Implement this process
        
        # Find all possible moves
        moves = self.findMoves(wrld)
        
        # Calculate Q-value of each possible action
        maxQ = -999.0
        bestMove = None
        for m in moves:
            # TODO: Adjust calcQ to include bomb location if bomb is placed (change m[0] to m)
            qVal = self.calcMaxQ(wrld, m[0], wfs)
            if qVal > maxQ:
                maxQ = qVal
                bestMove = m
            
        # TODO: At random, pick a random action so the agent keeps exploring
        
        # Take the action with the highest value
        # Place bomb if bomb flag is true
        if bestMove[1] == True:
            CharacterEntity.place_bomb()
        
        x = bestMove[0][0] - char[0]
        y = bestMove[0][1] - char[0]
        
        self.move(x, y)

        # Calculate new features and put it in weight-feature pairs
        # TODO: Find out if this should be calculated based on prev or new position
        char = self.findChar(wrld)
        wfs = self.calcAllFeatures(wrld, char, wfs)

        # Calculate reward of current pose
        # TODO: Same as above, figure out if prev or new
        reward = self.calcReward(wrld, char)

        # Update all weights
        wfs = self.updateWeights(wrld, wfs, char, reward)

        # Store weights in file
        f1 = open(file_path, "w") # Write
        for w in wfs:
            f1.write(f"{w[0]}\n")


    def findMoves(self, wrld):
        # Determine all possible actions (do nothing, place bomb, move in all 8 directions, or move and place bomb)
        moves = []
        char = self.findChar(wrld)
        bomb = self.findBomb(wrld) # Check if bomb exists (cannot place new bomb)

        # Identify possible neighboring moves
        neighbors = self.getNeighbors8(wrld, char)
        
        # Add moves to do nothing and place bomb
        moves.append(char, False) # Stay still, don't place bomb
        if bomb is not None: moves.append(char, True) # Stay still, place bomb
        
        # Add moves for all neighbors
        for n in neighbors:
            moves.append(n, False)
            if bomb is not None: moves.append(n, True)


    # ==================== Approximate Q-Learning ====================

    ''' This function defines how approximate Q-learning behaves overall (i starts at 0) '''
    def calcFeature(self, wrld, cell, featureNum):
        match featureNum:

            case 0: # Number of walls surrounding
                return 1 / (1 + 8 - len(self.getNeighbors8(wrld, cell)))
            
            case 1:
                return 0.5
            
            case _: # Default
                return 0

    def calcAllFeatures(self, wrld, cell, wfs):
        
        # Iterate through each feature
        for i, f in enumerate(wfs):

            # Update feature value
            newF = self.calcFeature(wrld, cell, i)

            wfs[i] = (wfs[i][0], newF)

        return wfs

    def calcReward(self, wrld, char):
        mstr = self.findMstr(wrld)
        exit = wrld.exitcell

        if char == mstr:
            return self.deathReward - self.costOfLiving
        elif char == exit:
            return self.exitReward - self.costOfLiving
        else:
            return self.liveReward - self.costOfLiving

    ''' wfs [(Weight, Feature Value), ...]: Array containing weight-feature tuples '''
    def calcQ(self, wfs):

        # Q(s,a) = sum[wi*fi(s,a)]
        qSum = 0

        # Iterate through each weight-feature pair
        for w in wfs:

            # Add product of weight and feature to Q Value
            qSum += w[0] * w[1]

        return qSum

    def calcMaxQ(self, wrld, cell, wfs):

        # Get all possible moves
        neighbors = self.getNeighbors8(wrld, cell)

        # Store value of best move
        max = -999.0

        # Calculate Q-value of each move
        for n in neighbors:

            # Update feature values of neighboring cell and calculate Q-value
            newWfs = self.calcAllFeatures(wrld, n, wfs)
            qVal = self.calcQ(newWfs)

            # Set max value if larger
            if qVal > max: max = qVal

        return max

    def calcDelta(self, wrld, wfs, cell, reward):
        # Calculate Difference
        # Delta <-- [r + gamma*max_a'Q(s',a')] - Q(s,a)
        # r = Reward
        # gamma = Discount
        # max_a'Q(s',a') = Max action of all possible next moves
        # Q(s,a) = Q-value of move

        gamma = self.discount
        max_aQ = self.calcMaxQ(wrld, cell, wfs)
        q = self.calcQ(wfs)

        delta = reward + gamma * max_aQ - q

        return delta

    def updateWeights(self, wrld, wfs, cell, reward):
        # Calculate Weight
        # w_i <-- w_i + alpha * delta * f_i(s,a)
        # w_i = Previous weight
        # Alpha = Learning Rate
        # Delta = Difference
        # f_i(s,a) = Feature function

        # Update each weight
        for i, w in enumerate(wfs):

            delta = self.calcDelta(wrld, wfs, cell, reward)
            func = self.calcFeature(wrld, cell, i)
            alpha = self.learnRate

            # Update weight in wfs array
            wi = w[0] + alpha * delta * func

            wfs[i] = (wi, w[1])

        return wfs














    # def do(self, wrld):

    #     # Locate entities and exit coordinates
    #     char = self.findChar(wrld)
    #     mstr = self.findMstr(wrld)
    #     exit = wrld.exitcell
        
    #     # Determine which direction the monster is moving in
    #     m = next(iter(wrld.monsters.values()))
    #     self.mstrMovement = (m[0].dx, m[0].dy)
        
    #     # Define expectimax start and depth variables
    #     depth = 4
    #     mstrDist = 6

    #     # Define weights for expectimax states and actions
    #     self.deathCost = -999
    #     self.mstrWeight = 10
    #     self.exitWeight = 10
    #     self.mstrChaseDist = 2.8
    #     self.mstrChaseCost = 100

    #     # Use A* or expectimax depending on monster proximity
    #     distToMstr = len(self.aStar(wrld, char, mstr))
        
    #     if distToMstr < mstrDist:
    #         nextStep = self.expectimax(wrld, char, mstr, exit, depth)

    #     else:
    #         result = self.aStar(wrld, char, exit)
    #         nextStep = result.pop()
    #         nextStep = result.pop()

    #     # Execute best move
    #     (cx, cy) = char
    #     (nx, ny) = nextStep
    #     (x, y) = (nx-cx, ny-cy)
    #     self.move(x, y)

    # def evaluatePose(self, wrld, char, mstr, exit):
        
    #     # Calculate score of a state given character distance to monster and exit
    #     mstrDist = self.euclideanDistance(char, mstr)
        
    #     score = 0
    #     score += mstrDist * self.mstrWeight
    #     score -= len(self.aStar(wrld, char, exit)) * self.exitWeight
        
    #     # Only add this score if the monster will start deterministically chasing
    #     if mstrDist < self.mstrChaseDist:
    #         score -= 1 / mstrDist * self.mstrChaseCost
        
    #     return score

    def findChar(self, wrld):
        return wrld.me(self).x, wrld.me(self).y

    def findMstr(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if wrld.monsters_at(x, y):
                    return (x, y)

        return None
    
    def findBomb(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if wrld.bomb_at(x, y):
                    return (x, y)
        
        return None

    # def mstrAtWall(self, wrld, mstr):
                
    #     # Define position after next move
    #     x = mstr[0] + self.mstrMovement[0]*2
    #     y = mstr[1] + self.mstrMovement[1]*2        
        
    #     # Check if next move is in a wall or barrier
    #     width = wrld.width()
    #     height = wrld.height()
        
    #     # Check if next cell is a barrier
    #     if (x<0 or x>width-1) or (y<0 or y>height-1) or wrld.wall_at(x, y):
    #         return True
        
    #     return False
    

    # # ======== Expectimax ========
    # def expectimax(self, wrld, char, mstr, exit, depth):
        
    #     # Run expectimax of all surrounding values
    #     cells = self.getNeighbors8(wrld, char)

    #     maxVal = float("-inf")
    #     maxCell = None
    #     for cell in cells:
    #         val = self.expValue(wrld, cell, mstr, exit, depth)
    #         val += -len(self.aStar(wrld, cell, exit))
                    
    #         if val > maxVal:
    #             maxVal = val
    #             maxCell = cell

    #     # Return arg max (the state/action responsible for the max value)
    #     return maxCell

    # def expValue(self, wrld, char, mstr, exit, depth):
        
    #     # If on monster tile, return death cost
    #     if char == mstr:
    #         return self.deathCost

    #     # If at end of depth, return low value to deter overextending
    #     if depth == 0:
    #         return self.evaluatePose(wrld, char, mstr, exit)

    #     # Set utility value = 0
    #     val = 0

    #     # If within monster chasse distance, monster moves deterministically
    #     if self.euclideanDistance(char, mstr) <= self.mstrChaseDist:
            
    #         # Calculate ideal monster move
    #         x = char[0] - mstr[0]
    #         y = char[1] - mstr[1]
            
    #         # Clamp movement
    #         x = max(-1, min(x, 1))
    #         y = max(-1, min(x, 1))
            
    #         next = (mstr[0]+x, mstr[1]+y)
            
    #         if next == char:
    #             val += self.deathCost
    #         else:
    #             # Value = Value + probability * maxValue(state, action)
    #             val += self.expectiMaxValue(wrld, char, next, exit, depth-1)
                
    #             # Subtract from score if monster is chasing
    #             val -= self.mstrChaseCost
        
    #     # If at wall, monster moves randomly in direction with probability of 1/(possible moves)
    #     elif self.mstrAtWall(wrld, mstr):
            
    #         # For every action in the state:
    #         mstrCells = self.getNeighbors8(wrld, mstr)
    #         p = 1 / len(mstrCells)
    #         for cell in mstrCells:
    #             # Calculate probability of hitting monster for each action
    #             if cell == char:
    #                 val += p * self.deathCost
    #             else:
    #                 # Value = Value + probability * maxValue(state, action)
    #                 val += p * self.expectiMaxValue(wrld, char, cell, exit, depth-1)
                    
    #     # If outside two cells, monster moves deterministically
    #     else:
                        
    #         # Calculate next monster move
    #         x = mstr[0] + self.mstrMovement[0]
    #         y = mstr[1] + self.mstrMovement[1]
                        
    #         next = (x, y)
            
    #         if next == char:
    #             val += self.deathCost
    #         else:
    #             # Value = Value + probability * maxValue(state, action)
    #             val += self.expectiMaxValue(wrld, char, next, exit, depth-1) 

    #     # Return utility value
    #     return val

    # def expectiMaxValue(self, wrld, char, mstr, exit, depth):
        
    #     # If at exit or max depth, return utility
    #     if char == exit:
    #         return 1000
        
    #     # If at end of depth, return low value to deter overextending
    #     if depth == 0:
    #         return self.evaluatePose(wrld, char, mstr, exit)
        
    #     # Set utility value to -inf
    #     val = float("-inf")

    #     # For every action in the state:
    #     charCells = self.getNeighbors8(wrld, char)
    #     for cell in charCells:
    #         # Value = max(value, expectiValue(state, action))
    #         val = max(val, self.expValue(wrld, cell, mstr, exit, depth-1))

    #     # Return utility value
    #     return val

    # # ======== A* Calculations ========

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

    # def euclideanDistance(self, a, b):
    #     return sqrt( (a[0] - b[0])**2 + (a[1] - b[1])**2 )

    # def aStar(self, wrld, start, goal):

    #     # Define A* variables
    #     frontier    = PriorityQueue()
    #     came_from   = {}
    #     cost_so_far = {}

    #     # Set start node
    #     frontier.put((0, start))
    #     came_from[start]   = None
    #     cost_so_far[start] = 0

    #     while not frontier.empty():

    #         # Remove highest prioririty item from frontier
    #         current = frontier.get()[1]

    #         # Exit loop if at goal
    #         if current == goal: break

    #         # Check neighbors of current node
    #         for next in self.getNeighbors8(wrld, current):

    #             # Calculate move cost to next node
    #             new_cost = cost_so_far[current] + self.euclideanDistance(current, next)

    #             # If next wasn't visited or the path to next is cheaper than the existing:
    #             if (next not in cost_so_far) or (new_cost < cost_so_far[next]):

    #                 # Set cost, calculate heuristic, and store in queue
    #                 cost_so_far[next] = new_cost
    #                 priority          = new_cost + self.euclideanDistance(goal, next)
    #                 frontier.put((priority, next))
    #                 came_from[next]   = current

    #     # Fill path
    #     path = []

    #     while current is not None:

    #         # Backtrack from current node to get to original
    #         path.append(current)
    #         current = came_from[current]

    #     return path