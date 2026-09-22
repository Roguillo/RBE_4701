import math
import sys

sys.path.insert(0, '../bomberman')

import numpy as np
from entity import CharacterEntity  # type: ignore


class TestCharacter(CharacterEntity):
#--- General-Purpose ------------------------------------------------------------------------------------------------------------#
    
    ##
    # cell_a (x, y): first cell
    # cell_b (x, y): second cell
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
    # wrld [SensedWorld]: the world
    # cell (x, y)       : cell to look around for viable neighbors
    #
    # >>> returns list of valid cells to go to
    def get_neighbors_8(self, wrld, cell):
        cells = []

        for nx in [-1, 0, 1]:
            if (
                (cell[0] + nx >= 0)           and
                (cell[0] + nx <  wrld.width())
                ):
                for ny in [-1, 0, 1]:
                    if (
                        (
                            (cell[1] + ny >= 0)             and
                            (cell[1] + ny <  wrld.height())

                        ) and not(
                            wrld.wall_at(cell[0] + nx, cell[1] + ny)

                        ) and not(
                            (nx == 0) and
                            (ny == 0)
                        )
                        ):
                            cells.append((cell[0] + nx, cell[1] + ny))
        return(cells)

#--- Expectimax -----------------------------------------------------------------------------------------------------------------#

    # max depth/amount of tree layers to explore (full turns)
    search_depth = 3

    ##
    # wrld [SensedWorld]: given world state
    #
    # >>> returns list of monster positions found
    def find_monsters(self, wrld):
        monsters = []

        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.monsters_at(x, y)): monsters.append((x, y))

        return(monsters)

    ##
    # exit          {absolute}(x, y): exit cell
    # character_pos {absolute}(x, y): given character position
    # monster_pos   {absolute}(x, y): given monster position
    # depth                   [int] : current search depth
    #
    # >>> returns whether the search is at a terminal state and should end
    def terminal(self, exit, character_pos, monster_pos, depth):
        return(
            (character_pos == exit)              or
            (character_pos == monster_pos)       or
            (depth         >= self.search_depth)
            )

    ##
    # exit          {absolute}(x, y): exit cell
    # character_pos {absolute}(x, y): given character position
    # monster_pos   {absolute}(x, y): given monster position
    # depth                   [int] : current search depth
    #
    # >>> returns node utility
    def utility(self, exit, character_pos, monster_pos, depth):
        # getting to the exit sooner is better
        if(character_pos == exit)       : return( 100 - depth)
        # dying is bad
        if(character_pos == monster_pos): return(-100)

        # ratio of exit approach vs. monster avoidance
        k = 1.0

        # over max search depth
        if(depth         >= self.search_depth):
            exit_dist    = self.euclid_dist(character_pos, exit)
            monster_dist = self.euclid_dist(character_pos, monster_pos)

            return(-(k * exit_dist) + ((1 - k) * monster_dist))

    ##
    # wrld                  [SensedWorld]: given world state
    # monster_pos {absolute}(x, y)       : given monster position
    # action      {absolute}(x, y)       : given action
    # who                   [boolean]    : whom to move {True -> Character, False -> Monster}
    #
    # >>> moves corresponding agent in hypothetical world, returns said world, new character position, and new monster position
    def result(self, wrld, monster_pos, action, who):
        hypth_wrld    = wrld.from_world(wrld)
        character     = hypth_wrld.me(self)
        character_pos = (character.x, character.y)
        monster       = hypth_wrld.monsters_at(monster_pos[0], monster_pos[1])[0]

        # move character
        if(who):
            character.move(action[0] - character_pos[0], action[1] - character_pos[1])
            hypth_wrld.update_character_move(character, True)
            new_character_pos = (character.x, character.y)
            new_monster_pos   = monster_pos

        # move monster
        else   :
            monster.move(  action[0] - monster_pos[0]  , action[1] - monster_pos[1])
            hypth_wrld.update_monster_move(monster, True)
            new_character_pos = character_pos
            new_monster_pos   = (monster.x, monster.y)

        return(hypth_wrld, new_character_pos, new_monster_pos)

    ##
    # wrld                       [SensedWorld]: given world state
    # exit             {absolute}(x, y)       : exit cell
    # character_pos    {absolute}(x, y)       : given character position
    # monster_pos      {absolute}(x, y)       : given monster position
    # doing_expectimax          [boolean]     : whether to recurse with a min (minimax) or chance (expectimax) node next
    # depth                     [int]         : current search depth
    #
    # >>> returns found node utility
    def max_node(self, wrld, exit, character_pos, monster_pos, doing_expectimax, depth):
        # get utility if terminal
        if(self.terminal(exit, character_pos, monster_pos, depth)):
            return(self.utility(exit, character_pos, monster_pos, depth))

        # start off with $-\infty$
        val = float("-inf")

        # consider character moves
        for action in self.get_neighbors_8(wrld, character_pos):
            (hypth_wrld, new_character_pos, new_monster_pos) = self.result(wrld, monster_pos, action, True)

            # call chance node if running expectimax, min node if running minimax
            if(doing_expectimax): val = max(val, self.chance_node(hypth_wrld, exit, new_character_pos, new_monster_pos, depth + 1))
            else                : val = max(val, self.min_node(hypth_wrld, exit, new_character_pos, new_monster_pos, depth + 1))

        return(val)

    ##
    # wrld                       [SensedWorld]: given world state
    # exit             {absolute}(x, y)       : exit cell
    # character_pos    {absolute}(x, y)       : given character position
    # monster_pos      {absolute}(x, y)       : given monster position
    # depth                      [int]        : current search depth
    #
    # >>> returns found node utility
    def min_node(self, wrld, exit, character_pos, monster_pos, depth):
        # get utility if terminal
        if(self.terminal(exit, character_pos, monster_pos, depth)):
            return(self.utility(exit, character_pos, monster_pos, depth))

        # start off with $\infty$
        val = float("inf")

        # consider monster moves
        for action in self.get_neighbors_8(wrld, monster_pos):
            (hypth_wrld, new_character_pos, new_monster_pos) = self.result(wrld, monster_pos, action, False)
            val                                              = min(val, self.max_node(hypth_wrld, exit, new_character_pos, new_monster_pos, False, depth))

        return(val)

    ##
    # wrld                       [SensedWorld]: given world state
    # exit             {absolute}(x, y)       : exit cell
    # character_pos    {absolute}(x, y)       : given character position
    # monster_pos      {absolute}(x, y)       : given monster position
    # depth                      [int]        : current search depth
    #
    # >>> returns found node utility
    def chance_node(self, wrld, exit, character_pos, monster_pos, depth):
        # get utility if terminal
        if(self.terminal(exit, character_pos, monster_pos, depth)):
            return(self.utility(exit, character_pos, monster_pos, depth))

        # get monster moves
        monster_actions = self.get_neighbors_8(wrld, monster_pos)
        # start off with zero
        val             = 0
        # get probability from actions (all equally likely for monster wandering, whether stupid or not)
        prob            = 1.0 / len(monster_actions)

        # consider monster moves
        for action in monster_actions:
            (hypth_wrld, new_character_pos, new_monster_pos)  = self.result(wrld, monster_pos, action, False)
            val                                              += prob * self.max_node(hypth_wrld, exit, new_character_pos, new_monster_pos, True, depth)

        return(val)

    ##
    # wrld [SensedWorld]: sensed world state
    #
    # >>> returns best action to take
    def root_node(self, wrld):
        exit          = wrld.exitcell
        character_pos = (self.x, self.y)
        monsters      = self.find_monsters(wrld)
        actions       = self.get_neighbors_8(wrld, character_pos)
        dists         = []
        vals          = []

        # get closest monster and distance to it
        for monster in monsters: dists.append(self.euclid_dist(character_pos, monster))
        dist_to_monster = min(dists)
        monster_pos     = monsters[np.argmin(dists)]

        # consider character actions
        for action in actions:
            (hypth_wrld, new_character_pos, new_monster_pos) = self.result(wrld, monster_pos, action, True)

            # run expectimax if far enough away from the closest monster, minimax otherwise
            if(dist_to_monster < 2.83): vals.append(self.min_node(hypth_wrld, exit, new_character_pos, new_monster_pos, 1))
            else                      : vals.append(self.chance_node(hypth_wrld, exit, new_character_pos, new_monster_pos, 1))

        best_action = actions[np.argmax(vals)]
            
        return(best_action[0] - character_pos[0], best_action[1] - character_pos[1])

#--- Main Loop ------------------------------------------------------------------------------------------------------------------#

    ##
    # wrld: world state
    #
    # >>> actions to be completed in a timestep of gameplay
    def do(self, wrld): 
        the_play = self.root_node(wrld)
        self.move(the_play[0], the_play[1])
