# This is necessary to find the main code
import sys
import time

sys.path.insert(0, '../../bomberman')
sys.path.insert(1, '..')

import random

from game import Game
from monsters.stupid_monster import StupidMonster

# TODO This is your code!
sys.path.insert(1, '../teamNN')
from testcharacter import TestCharacter

# Create the game
random.seed(int(time.time())) # TODO Change this if you want different random choices
g = Game.fromfile('map.txt')
g.add_monster(StupidMonster("stupid", # name
                            "S",      # avatar
                            3, 9      # position
))

# TODO Add your character
g.add_character(TestCharacter("jebediah", # name
                              "C",  # avatar
                              0, 0  # position
))

# Run!
g.go(1)
