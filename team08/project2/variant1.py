# This is necessary to find the main code
import sys
sys.path.insert(0, '../../bomberman')
sys.path.insert(1, '..')

# Import necessary stuff
from game import Game

# TODO This is your code!
sys.path.insert(1, '../teamNN')
from testcharacter2 import TestCharacter


# Create the game
g = Game.fromfile('map.txt')

# TODO Add your character
c = TestCharacter("me", # name
                              "C",  # avatar
                              0, 0  # position
)

g.add_character(c)

# Run!
g.go(1)
