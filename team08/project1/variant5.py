# This is necessary to find the main code
import sys
sys.path.insert(0, '../../bomberman')
sys.path.insert(1, '..')

# Import necessary stuff
import random
from game import Game
from monsters.stupid_monster import StupidMonster
from monsters.selfpreserving_monster import SelfPreservingMonster

# TODO This is your code!
sys.path.insert(1, '../team08')
from testcharacter import TestCharacter

wins=0
# Create the game
for i in range(20):
    g = Game.fromfile('map.txt')
    g.add_monster(StupidMonster("stupid", # name
                                "S",      # avatar
                                3, 5,     # position
    ))
    g.add_monster(SelfPreservingMonster("aggressive", # name
                                        "A",          # avatar
                                        3, 13,        # position
                                        1             # detection range
    ))

    variant = 5
    c = TestCharacter("me", # name
                                "C",  # avatar
                                0, 0  # position
    )
    c.setVariant(variant)
    # TODO Add your character
    g.add_character(c)



    # Run!
    g.go(1)
    for event in g.events:
        print(event)
        if event.tpe == event.CHARACTER_FOUND_EXIT:
            wins+=1
            print("Win")

print("Win/Lose ration: " + str(wins/20))