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
        print(char)
        mstr = self.findMstr(wrld)
        print(mstr)
        exit = wrld.exitcell
        print(exit)

        path = self.aStar(wrld, char, mstr)

        print(len(path)-1)

        # minimaxDepth = 2
        # minimaxEnableDist = 5

        # char = self.findChar(wrld)
        # print(char)
        # mstr = self.findMstr(wrld)
        # print(mstr)
        # exit = wrld.exitcell
        # print(exit)

        # result = self.a_star(wrld, (0, 0), mstr)
        # print(result)
        # charMstrDist = len(result) - 1

        # if (charMstrDist <= minimaxEnableDist):
        #     print("Close!")
        #     print(charMstrDist)
        # else:
        #     print("Far!")
        #     print(charMstrDist)








        
        

        # targetMstrDist = 4
        # mstrDistWeight = 5

        # # Iterate through eight cells surrounding player
        # # Give each cell a score as a sum of dist to goal
        # # and distance to monster
        # cells = self.get_neighbors_8(wrld, char)
        # minScore = 999
        # bestMove = None
        # for cell in cells:
        #     score = len(self.a_star(wrld, cell, exit))

        #     cellMstrDist = self.euclidean_distance(cell, mstr)

        #     if cellMstrDist <= targetMstrDist:
        #         score += (targetMstrDist - cellMstrDist + 1) * mstrDistWeight

        #     print(cell, score, cellMstrDist)

        #     if score < minScore:
        #         minScore = score
        #         bestMove = cell



        # path = self.a_star(wrld, char, exit)
        # exitDist = len(path)

        # next = path.pop()
        # next = path.pop()

        # (cx, cy) = char
        # (nx, ny) = bestMove
        # (x, y) = (nx-cx, ny-cy)
        # self.move(x, y)


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
    def minimax(self, wrld, depth):
        pass


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
                    cells.append((cell[0] + nx, cell[1] + ny))
                    
        return cells

    def euclideanDistance(self, cell_a, cell_b):
        return sqrt( (cell_a[0] - cell_b[0])**2 + (cell_a[1] - cell_b[1])**2 )

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

        path.reverse()
        return(path)