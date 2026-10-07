# This is necessary to find the main code
import sys
import math
import random
from queue import PriorityQueue
sys.path.insert(0, '../bomberman')
# Import necessary stuff
from entity import CharacterEntity
from sensed_world import SensedWorld 
from colorama import Fore, Back
import os

class TestCharacter(CharacterEntity):

    weights = []

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'weights3.txt')

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                row = [float(x) for x in line.strip().split()]
                weights.append(row)

    else:
        print("File not found!")

    wE = 1
    wM = -2
    wX = -5
    wB = -4
    wW = 3
    weights = [[1.0, -2.0, -5.0, -4.0, 3.0] for _ in range(9)]

    curiosity = 0.3

    rows, cols = (8*19, 9)
    qValues = [[0] * 9 for _ in range(rows)]



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

    def find_explosion(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.explosion_at(x, y)): return((x, y))

        return(None)

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



    def genFeature(self, featNum, wrld, me):
        match featNum:
            case 0:
                exit = self.find_exit(wrld)
                dist = self.euclidean_distance((me.x, me.y),(exit[0], exit[1]))
                return 1/((dist)+1)
            case 1:
                exit = self.find_monster(wrld)
                dist = 0
                try:
                    dist = self.euclidean_distance((me.x, me.y),(exit[0], exit[1]))
                except:
                    pass
                return 1/((dist)+1)
            case 2:
                exit = self.find_explosion(wrld)
                dist = 0
                try:
                    dist = self.euclidean_distance((me.x, me.y),(exit[0], exit[1]))
                except:
                    pass
                return 1/((dist)+1)
            case 3:
                return 1/((self.numWalls(wrld))+1)
            case 4:
                exit = self.find_bomb(wrld)
                dist = 0
                try:
                    dist = self.euclidean_distance((me.x, me.y),(exit[0], exit[1]))
                except:
                    pass
                return 1/((dist)+1)
        

    def getBestQValue(self, char, wrld, qValues):
        posMoves = self.get_pos_moves(char, wrld)
        bestMove = [0, 0]
        bestValue = -999
        for move in posMoves:
            moveValue = -999
            match move:
                case [-1,-1]:
                     moveValue = qValues[char.y*8+char.x][0]
                case [0,-1]:
                     moveValue = qValues[char.y*8+char.x][1]
                case [1,-1]:
                     moveValue = qValues[char.y*8+char.x][2]
                case [-1,0]:
                     moveValue = qValues[char.y*8+char.x][3]
                case [1,0]:
                     moveValue = qValues[char.y*8+char.x][4]
                case [-1,1]:
                     moveValue = qValues[char.y*8+char.x][5]
                case [0,1]:
                     moveValue = qValues[char.y*8+char.x][6]
                case [1,1]:
                     moveValue = qValues[char.y*8+char.x][7]
                case [0,0]:
                     moveValue = qValues[char.y*8+char.x][8]
            if moveValue > bestValue:
                bestMove = move
                bestValue = moveValue
            elif moveValue == bestValue and random.random() < 0.5:
                bestMove = move
        return bestValue

    def getBestQValueMove(self, char, wrld, qValues):
            posMoves = self.get_pos_moves(char, wrld)
            bestMove = posMoves[random.randint(0, len(posMoves)-1)]
            bestValue = -999
            for move in posMoves:
                moveValue = -999
                match move:
                    case [-1,-1]:
                         moveValue = qValues[char.y*8+char.x][0]
                    case [0,-1]:
                         moveValue = qValues[char.y*8+char.x][1]
                    case [1,-1]:
                         moveValue = qValues[char.y*8+char.x][2]
                    case [-1,0]:
                         moveValue = qValues[char.y*8+char.x][3]
                    case [1,0]:
                         moveValue = qValues[char.y*8+char.x][4]
                    case [-1,1]:
                         moveValue = qValues[char.y*8+char.x][5]
                    case [0,1]:
                         moveValue = qValues[char.y*8+char.x][6]
                    case [1,1]:
                         moveValue = qValues[char.y*8+char.x][7]
                    case [0,0]:
                         moveValue = qValues[char.y*8+char.x][8]
                if moveValue > bestValue:
                    bestMove = move
                    bestValue = moveValue
                elif moveValue == bestValue and random.random() < 0.5:
                    bestMove = move
            return bestMove




    

    def approximateQLearning(self, wrld, qValues, alpha, rewards):     
        for i in range(40):
            (x, y) = (self.x, self.y)
            newwrld = SensedWorld.from_world(wrld)
            events = newwrld.events

            players = newwrld.characters_at(x, y)

            if players is None:
                print("ERROR: No player at expected position!")
                return [0, 0]

            newPlayer = players[0]
            dead = False
            gamma = 0.9
            moves = 0
            while not(dead) and moves < 100:    
                eF = self.genFeature(0, newwrld, newPlayer)
                mF = self.genFeature(1, newwrld, newPlayer)
                xF = self.genFeature(2, newwrld, newPlayer)
                wF = self.genFeature(3, newwrld, newPlayer)
                bF = self.genFeature(4, newwrld, newPlayer)
                posMoves = self.get_pos_moves(newPlayer, newwrld)
                if random.random() < self.curiosity:
                    moveSelection = random.randint(0, len(posMoves)-1)
                    a = posMoves[moveSelection]
                else:
                    a = self.getBestQValueMove(newPlayer, newwrld, qValues)

                (old_x, old_y) = (newPlayer.x, newPlayer.y)
                newPlayer.move(a[0], a[1])
                (new_x, new_y) = (newPlayer.x, newPlayer.y)
                reward = rewards[new_y][new_x]
                for event in events:
                    if event.tpe == 4:
                        reward = 500
                        dead = True
                    elif event.tpe == 3:
                        reward = -1000
                        dead = True
                    elif event.tpe == 2:
                        reward = -15000
                        dead = True
                    elif event.tpe == 1:
                        reward = 1000
                    elif event.tpe == 0:
                        reward = 600
                    
                match a:
                    case [-1,-1]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][0]
                        self.weights[0] = [self.weights[0][0] + (alpha*delta*eF), self.weights[0][1] + (alpha*delta*mF), self.weights[0][2] + (alpha*delta*xF), self.weights[0][3] + (alpha*delta*bF), self.weights[0][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][0] = self.weights[0][0]*eF + self.weights[0][1]*mF + self.weights[0][2]*xF + self.weights[0][3]*bF + self.weights[0][4]*wF
                    case [0,-1]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][1]
                        self.weights[1] = [self.weights[1][0] + (alpha*delta*eF), self.weights[1][1] + (alpha*delta*mF), self.weights[1][2] + (alpha*delta*xF), self.weights[1][3] + (alpha*delta*bF), self.weights[1][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][1] = self.weights[1][0]*eF + self.weights[1][1]*mF + self.weights[1][2]*xF + self.weights[1][3]*bF + self.weights[1][4]*wF
                    case [1,-1]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][2]
                        self.weights[2] = [self.weights[2][0] + (alpha*delta*eF), self.weights[2][1] + (alpha*delta*mF), self.weights[2][2] + (alpha*delta*xF), self.weights[2][3] + (alpha*delta*bF), self.weights[2][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][2] = self.weights[2][0]*eF + self.weights[2][1]*mF + self.weights[2][2]*xF + self.weights[2][3]*bF + self.weights[2][4]*wF
                    case [-1,0]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][3]
                        self.weights[3] = [self.weights[3][0] + (alpha*delta*eF), self.weights[3][1] + (alpha*delta*mF), self.weights[3][2] + (alpha*delta*xF), self.weights[3][3] + (alpha*delta*bF), self.weights[3][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][3] = self.weights[3][0]*eF + self.weights[3][1]*mF + self.weights[3][2]*xF + self.weights[3][3]*bF + self.weights[3][4]*wF
                    case [1,0]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][4]
                        self.weights[4] = [self.weights[4][0] + (alpha*delta*eF), self.weights[4][1] + (alpha*delta*mF), self.weights[4][2] + (alpha*delta*xF), self.weights[4][3] + (alpha*delta*bF), self.weights[4][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][4] = self.weights[4][0]*eF + self.weights[4][1]*mF + self.weights[4][2]*xF + self.weights[4][3]*bF + self.weights[4][4]*wF
                    case [-1,1]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][5]
                        self.weights[5] = [self.weights[5][0] + (alpha*delta*eF), self.weights[5][1] + (alpha*delta*mF), self.weights[5][2] + (alpha*delta*xF), self.weights[5][3] + (alpha*delta*bF), self.weights[5][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][5] = self.weights[5][0]*eF + self.weights[5][1]*mF + self.weights[5][2]*xF + self.weights[5][3]*bF + self.weights[5][4]*wF
                    case [0,1]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][6]
                        self.weights[6] = [self.weights[6][0] + (alpha*delta*eF), self.weights[6][1] + (alpha*delta*mF), self.weights[6][2] + (alpha*delta*xF), self.weights[6][3] + (alpha*delta*bF), self.weights[6][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][6] = self.weights[6][0]*eF + self.weights[6][1]*mF + self.weights[6][2]*xF + self.weights[6][3]*bF + self.weights[6][4]*wF
                    case [1,1]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][7]
                        self.weights[7] = [self.weights[7][0] + (alpha*delta*eF), self.weights[7][1] + (alpha*delta*mF), self.weights[7][2] + (alpha*delta*xF), self.weights[7][3] + (alpha*delta*bF), self.weights[7][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][7] = self.weights[7][0]*eF + self.weights[7][1]*mF + self.weights[7][2]*xF + self.weights[7][3]*bF + self.weights[7][4]*wF
                    case [0,0]:
                        delta = (reward + gamma*(self.getBestQValue(newPlayer, newwrld, qValues))) - qValues[(old_y*8)+old_x][8]
                        self.weights[8] = [self.weights[8][0] + (alpha*delta*eF), self.weights[8][1] + (alpha*delta*mF), self.weights[8][2] + (alpha*delta*xF), self.weights[8][3] + (alpha*delta*bF), self.weights[8][4] + (alpha*delta*wF)]
                        qValues[old_y*8+old_x][8] = self.weights[8][0]*eF + self.weights[8][1]*mF + self.weights[8][2]*xF + self.weights[8][3]*bF + self.weights[8][4]*wF
                        newPlayer.place_bomb()
                moves += 1
                (x, y) = (new_x, new_y)
                newwrld = SensedWorld.from_world(wrld)
                

            """print("Q-Values after move:")
            for i in range(len(self.qValues)):
                print(self.qValues[i])"""
        with open(self.file_path, "w") as file:
            for row in self.weights:
                line = " ".join(map(str, row))
                file.write(line + "\n")

        return self.getBestQValueMove(self, wrld, qValues)


    
    def do(self, wrld):
        # Your code here
        exit = self.find_exit(wrld)
        
        goal = exit
        if(self.y < 4):
            goal = (4, 6)

        elif(self.y >= 4 and self.y < 8):
            goal = (4, 10)

        elif(self.y >= 8 and self.y < 12):
            goal = (4, 14)

        elif(self.y >= 12 and self.y < 16):
            goal = (4, 18)

        path = self.a_star(wrld, (self.x, self.y), goal)
        r = self.genSpaceReward(wrld, path)
        print(path)

        if path[-1] == goal:
            p = self.policyIteration(wrld, r, 0.9)
            bestMovement = p[self.y][self.x]
        else: 
            p = self.approximateQLearning(wrld, self.qValues, 0.9, r)
            bestMovement = p

        if bestMovement == [0, 0] and self.find_bomb(wrld) is None:
            self.place_bomb()
            print("Placed bomb")
        else:
            if(len(path) <= 5):
                bestMovement = [path[1][0] - self.x, path[1][1] - self.y]
            print(bestMovement)
            self.move(bestMovement[0], bestMovement[1])

