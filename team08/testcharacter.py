import math
import sys
from queue import PriorityQueue

sys.path.insert(0, '../bomberman')

from entity import CharacterEntity  # type: ignore


class TestCharacter(CharacterEntity):
    def find_exit(self, wrld):
        for x in range(wrld.width()):
            for y in range(wrld.height()):
                if(wrld.exit_at(x, y)): return((x, y))

        return(None)
         
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

    def a_star(self, wrld):
        frontier    = PriorityQueue()
        came_from   = {}
        cost_so_far = {}

        start = (self.x, self.y)
        goal  = self.find_exit(wrld)

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
    
    def do(self, wrld):
        path = self.a_star(wrld)

        if(len(path) <= 1): return

        self.move(path[1][0] - self.x, path[1][1] - self.y)
