# This is necessary to find the main code
import sys
sys.path.insert(0, '../../bomberman')
sys.path.insert(1, '..')

# Import necessary stuff
import random
from game import Game
from monsters.stupid_monster import StupidMonster

# TODO This is your code!
sys.path.insert(1, '../teamNN')
from testcharacter2 import TestCharacter

# Create the game

g = Game.fromfile('map.txt')
g.add_monster(StupidMonster("stupid", # name
                            "S",      # avatar
                            3, 9      # position
))

# TODO Add your character
c = TestCharacter("me", # name
                              "C",  # avatar
                              0, 0  # position
)

g.add_character(c)

# Run!
g.go(1)
