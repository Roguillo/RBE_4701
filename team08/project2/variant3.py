# This is necessary to find the main code
import sys
sys.path.insert(0, '../../bomberman')
sys.path.insert(1, '..')

# Import necessary stuff
import random
from game import Game
from monsters.selfpreserving_monster import SelfPreservingMonster

# TODO This is your code!
sys.path.insert(1, '../teamNN')
from testcharacter import TestCharacter

ratio = 0.0
while ratio < 50.0:
    ratio = 0.0
    wins = 0
    loses = 0
    for i in range(10):
        g = Game.fromfile('map.txt')
        g.add_monster(SelfPreservingMonster("selfpreserving", # name
                                            "S",              # avatar
                                            3, 9,             # position
                                            1                 # detection range
        ))

        # TODO Add your character
        g.add_character(TestCharacter("me", # name
                                    "C",  # avatar
                                    0, 0  # position
        ))
        # Run!
        g.go(1)
        for event in g.events:
            print(event)
            if event.tpe == 4:
                wins+=1
                print("Win")

    print("Wins: " + str(wins))
    print("Loses: " + str(10-wins))
    print("Win Ratio: " + str(wins/10))
    ratio = (wins/10)*100


