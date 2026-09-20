import math
import random
import sys
from queue import PriorityQueue

import numpy as np

sys.path.insert(0, '../bomberman')

from entity import CharacterEntity  # type: ignore


class TestCharacter(CharacterEntity):
    max_depth = 2

    ##
    # wrld: the world
    #
    # >>> returns list of exit cells found
    def find_exits(self, wrld):
        exits = []

        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.exit_at(x, y)): exits.append((x, y))

        return(exits)

    ##
    # wrld: the world
    #
    # >>> returns list of exit cells found
    def find_monsters(self, wrld):
        monsters = []

        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.monsters_at(x, y)): monsters.append((x, y))

        return(monsters)

    ##
    # wrld: the world
    # cell: cell to look around for viable neighbors
    #
    # >>> returns list of valid cells to go to
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

    ##
    # cell_a: first cell
    # cell_b: second cell
    #
    # >>> returns straight-line distance between given cells
    def euclid_dist(self, cell_a, cell_b):
        return(
            math.sqrt(
                (cell_a[0] - cell_b[0])**2 + 
                (cell_a[1] - cell_b[1])**2
                )
            )

    ##
    # cell_a: first cell
    # cell_b: second cell
    #
    # >>> returns edge cost between cells, currently set to use euclidean distance
    def get_edge_cost(self, cell_a, cell_b): return(self.euclid_dist(cell_a, cell_b))

    ##
    # cell_a: first cell
    # cell_b: second cell
    #
    # >>> returns edge cost between cells, currently set to use euclidean distance between given cell and exit
    def get_heuristic(self, goal, cell):     return(self.euclid_dist(goal, cell))

    ##
    # wrld: the world
    #
    # >>> returns list of cells composing the most optimal path to the exit
    def a_star(self, wrld):
        frontier    = PriorityQueue()
        came_from   = {}
        cost_so_far = {}

        start = (self.x, self.y)
        goal  = self.find_exits(wrld)[0]

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

        path      = []
        curr_cell = current
        
        while(curr_cell is not None):
            path.append(curr_cell)
            curr_cell = came_from[curr_cell]

        path.reverse()
        return(path)
    
    def result(self, wrld, action, who, depth):
        hypth_wrld = wrld.from_world(wrld)

        if(who == True):
            character = hypth_wrld.me(self)
            character.move(action[0], action[1])

            return(hypth_wrld.next()[0], depth)

        else:
            monster_pos     = self.find_monsters(hypth_wrld)[0]
            monster         = hypth_wrld.monsters_at(monster_pos[0], monster_pos[1])[0]
            monster.move(action[0] - monster_pos[0], action[1] - monster_pos[1])

            return(hypth_wrld.next()[0], depth + 1)

    def terminal(self, wrld, character_pos, monster_pos, depth):
        return(
            (wrld.exit_at(character_pos[0], character_pos[1]))     or
            (character_pos == monster_pos)    or
            (depth         >= self.max_depth)
            )

    def utility(self, wrld, character_pos, monster_pos, depth):
        if(character_pos == monster_pos): return(-25)
        if(wrld.exit_at(character_pos[0], character_pos[1])) : return( 20)
        if(depth >= self.max_depth)     : return(-self.euclid_dist(character_pos, self.find_exits(wrld)[0]))

        return(0)

    def max_node(self, wrld, character_pos, monster_pos, depth):
        if(self.terminal(wrld, character_pos, monster_pos, depth)):
            return(self.utility(wrld, character_pos, monster_pos, depth))
        
        val = float("-inf")

        for action in self.get_neighbors_8(wrld, character_pos):
            val = max(val, self.chance_node(wrld, action, monster_pos, depth))

        return(val)

    def chance_node(self, wrld, character_pos, monster_pos, depth):
        if(self.terminal(wrld, character_pos, monster_pos, depth)):
            return(self.utility(wrld, character_pos, monster_pos, depth))

        monster_actions = self.get_neighbors_8(wrld, monster_pos)
        val             = 0
        prob            = 1.0 / len(monster_actions)

        for action in monster_actions:
            val += prob * self.max_node(wrld, character_pos, action, depth + 1)

        return(val)

    def expectimax(self, wrld):
        character               = wrld.me(self)
        character_pos           = (character.x, character.y)
        monster_pos             = self.find_monsters(wrld)[0]
        (best_action, best_val) = ((0, 0), float("-inf"))

        for action in self.get_neighbors_8(wrld, character_pos):
            val = self.chance_node(wrld, action, monster_pos, 0)

            if(val) > best_val:
                best_val = val
                best_action = (action[0] - character_pos[0], action[1] - character_pos[1])

        return(best_action)

    ##
    # wrld: the world
    #
    # >>> actions to be completed in a timestep of gameplay
    def do(self, wrld): 
        the_play = self.expectimax(wrld)
        self.move(the_play[0], the_play[1])
