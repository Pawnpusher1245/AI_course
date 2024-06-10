import sys

from crossword import *
from collections import deque


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.crossword.variables:
            for word in list(self.domains[variable]):
                if len(word) != variable.length:
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revision = False
        to_remove = set()

        # Iterate over domain of x and y, track any inconsistent x:
        for val_x in self.domains[x]:
            consistent = False
            for val_y in self.domains[y]:
                if val_x != val_y and self.overlap_satisfied(x, y, val_x, val_y):
                    consistent = True
                    break

            if not consistent:
                to_remove.add(val_x)
                revision = True

        # Remove any domain variables that aren't arc consistent:
        self.domains[x] = self.domains[x] - to_remove
        return revision
    def overlap_satisfied(self, x, y, val_x, val_y):
            """
            Helper function that returns true if val_x and val_y
            satisfy any overlap arc consistency requirement for
            variables x and y.

            Returns True if consistency is satisfied, False otherwise.
            """

            # If no overlap, no arc consistency to satisfy
            if not self.crossword.overlaps[x, y]:
                return True

            # Otherwise check that letters match at overlapping indices
            else:
                x_index, y_index = self.crossword.overlaps[x,y]

                if val_x[x_index] == val_y[y_index]:
                    return True
                else:
                    return False

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            arcs = deque()
            for variable1 in self.crossword.variables:
                for variable2 in self.crossword.variables:
                    if variable1 != variable2:
                        arcs.append((variable1, variable2))
        
        while arcs:
            arc = arcs[0]
            arcs.popleft()
            variable1, variable2 = arc # Unpack the variables from arc

            # If we make a change, iterate through neighbors and add them
            if self.revise(variable1, variable2):
                if not self.domains[variable1]:
                    return False
                for neighbor in self.crossword.neighbors(variable1):
                    # We do not need to add variable 2 again
                    if neighbor != variable2:
                        arcs.append((neighbor, variable1))
        
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return len(assignment) == len(self.crossword.variables)
    
    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Check for word uniqueness in the assignment
        word_set = set()
        for variable, word in assignment.items():
            if word in word_set:
                return False
            word_set.add(word)

        # Check if word lengths match variable lengths
        for variable, word in assignment.items():
            if variable.length != len(word):
                return False

        # Check for conflicts between neighboring variables
        for variable1, word1 in assignment.items():
            for variable2, word2 in assignment.items():
                if variable1 != variable2:
                    overlap = self.crossword.overlaps.get((variable1, variable2))
                    if overlap:
                        i, j = overlap
                        if word1[i] != word2[j]:
                            return False

        return True

    def order_domain_values(self, var, assignment):
        unsorted_words = []
        neighbors = self.crossword.neighbors(var)
        for word1 in self.domains[var]:
            removed_words = 0
            for neighbor in neighbors:
                if neighbor not in assignment:
                    overlap_pair = self.crossword.overlaps.get((var, neighbor))
                    if overlap_pair is not None:
                        i, j = overlap_pair
                        for word2 in self.domains[neighbor]:
                            if word1[i] == word2[j]:
                                removed_words += 1
            unsorted_words.append((removed_words, word1))
        sorted_words = sorted(unsorted_words)
        return [word for _, word in sorted_words]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned_variables = [var for var in self.crossword.variables if var not in assignment]

        # Sort the unassigned variables by MRV (fewest remaining values in the domain)
        mrv_sorted = sorted(unassigned_variables, key=lambda var: len(self.domains[var]))

        return mrv_sorted[0]  # Return the variable with the fewest remaining values

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # If the assignment is complete, return it as the solution
        if self.assignment_complete(assignment):
            return assignment

        # Select an unassigned variable using variable selection heuristics
        var = self.select_unassigned_variable(assignment)

        # Iterate through the values in the domain of the selected variable
        for value in self.order_domain_values(var, assignment):
            # Create a copy of the assignment to avoid modifying the original
            new_assignment = assignment.copy()
            new_assignment[var] = value

            # Check if the new assignment is consistent
            if self.consistent(new_assignment):
                # Recursively call backtrack with the updated assignment
                result = self.backtrack(new_assignment)

                # If a solution is found, return it
                if result is not None:
                    return result

        # If no solution is found, backtrack by returning None
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
