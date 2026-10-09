# This is necessary to find the main code
import sys
import time
sys.path.insert(0, '../../bomberman')
sys.path.insert(1, '..')

# Import necessary stuff
import random
from game import Game
from monsters.selfpreserving_monster import SelfPreservingMonster

# TODO This is your code!
sys.path.insert(1, '../teamNN')
from testcharacter import TestCharacter

# Create the game
random.seed(int(time.time()))

gameCount = 20
winCount = 0
bombDeaths = 0
monsterDeaths = 0

for i in range(gameCount):
    g = Game.fromfile('map.txt')
    g.add_monster(SelfPreservingMonster("aggressive", # name
                                        "A",          # avatar
                                        # 3, 5,        # position
                                        3, 13,        # position
                                        2             # detection range
    ))

    # TODO Add your character
    g.add_character(TestCharacter("me", # name
                                "C",  # avatar
                                0, 0  # position
    ))

    # Run!
    g.go(1)

    for event in g.events:
        if event.tpe == 4:
            winCount += 1
        elif "killed itself" in str(event):
            bombDeaths += 1

print(f"Win/Loss Ratio: {winCount}/{gameCount - winCount}")
print(f"Exit found: {winCount}")
print(f"Bomb Deaths: {bombDeaths}")
print(f"Monster Deaths: {gameCount - winCount - bombDeaths}")
