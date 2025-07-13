from pathlib import Path
import argparse
    
def parse_formula_from_file(file_path: str):
    lines = ""
    with open(file_path) as file:
        lines = "\n".join(line.rstrip() for line in file)
    return parse_formula_from_string(lines)

def parse_formula_from_string(content: str):
    
    lines = content.split("\n")
    (num_vars, num_clauses) = lines[0].split(" ")[2:]

    formula = [set(map(int, clause.strip().split())) - {0} for clause in lines[1:]]
    return Formula(int(num_vars), formula)

# clauses only conain not-yet assigned variables
# check set() in clauses to check for empty clause = bottom, and clauses = [] for top
class Formula():
    
    def __init__(self,num_vars: int, clauses: list[set], debug: bool =False):
        self.num_vars = num_vars
        self.clauses = clauses # current clauses
        self.assignment = {}
        self.open_assignments = set(range(1, num_vars + 1))
        self.clauses_of_watched_literal = {i: set() for i in range(-num_vars, num_vars+1) if i != 0} # maps literal to clauses where it's watched
        self.watched_literals_in_clause = {}
        self.bcp_queue = []
        self.trail = [] # stores indices of assignment when decision 
        self.debug = debug

    def __str__(self):
        return "Clauses: [" + ", ".join(["{" + " ".join(map(str, clause)) + "}" for clause in self.clauses]) + "] \n" \
            + "Assignment: [" +  " ,".join(f"{var}={value}" for (var, value) in self.assignment.items())  + "]"

    # use e.g. -3 to set x3 to false
    def set_value_DEP(self, var: int):
        f = self.copy()
        f.num_vars = self.num_vars -1 # assigning a value removes one open variable
        f.assignment[abs(var)] = True if var > 0 else False
        f.open_assignments.remove(abs(var))

        new_clauses = []
        for clause in self.clauses:
            if var in clause:
                continue # this clause is true
            elif -var in clause:
                clause_copy = clause.copy()
                clause_copy.remove(-var)
                new_clauses.append(clause_copy)
            else:
                new_clauses.append(clause)
        f.clauses = new_clauses
        return f

    # copies the formula instance for the recursive call
    # copies everything, but only used in recursive implementation
    def copy(self):
        f =  Formula(self.num_vars, self.clauses, self.debug)
        f.assignment = self.assignment.copy()
        f.open_assignments = self.open_assignments.copy()
        f.clauses_of_watched_literal = self.clauses_of_watched_literal.copy()
        f.watched_literals_in_clause = self.watched_literals_in_clause.copy()
        f.bcp_queue = self.bcp_queue.copy()
        f.trail = self.trail.copy()
        return f


    #NOTE: only used in naiive recursive implementation
    def set_value(self, var:int):
        f = self.copy()
        f.assignment[abs(var)] = True if var > 0 else False
        f.open_assignments.remove(abs(var))
        return f


    # assigns a 
    def _assign_value(self, var: int, value: bool): 
        if abs(var) in self.assignment.keys():
            if self.debug:
                print(f"Assignment {var} : {self.assignment[abs(var)]} already exists")
            return False
        else:
            self.open_assignments.remove(abs(var)) # stores the literal as assigned

        self.assignment[abs(var)] = value if var > 0 else (not value) # store truth value
        self.trail.append(abs(var))  # store in assignment trail

        # self.bcp_queue.append(-var if value else var) # Don't do this, leads to infinite loop

        return True

    def remove_assignment(self, var: int):
        if abs(var) not in self.assignment.keys():
            if self.debug:
                print(f"Variable {var} is not assigned yet.")
            return False
        del self.assignment[var]
        self.open_assignments.add(abs(var))
        return True

    # adds the decision to the queue and calls bcp, assigning happens inside bcp
    def decide(self, lit: int, val: bool) -> bool:
        self.bcp_queue.append(lit if val else -lit)
        return self.bcp()
        

    def bcp(self):
        # do initial watchers setup

        if self.watched_literals_in_clause == {}:
            for i, clause in enumerate(self.clauses):
                clause_list = list(clause)
                lit1 = clause_list[0]
                self.clauses_of_watched_literal.setdefault(lit1, set()).add(i)
                self.watched_literals_in_clause.setdefault(i, set()).add(lit1)
                if len(clause_list) <= 1:
                    if lit1 in self.bcp_queue:
                        continue
                    elif -lit1 in self.bcp_queue:
                        self.bcp_queue = []
                        return False
                    else:
                        self.bcp_queue.append(lit1)
                else:
                    lit2 = clause_list[1]
                    self.clauses_of_watched_literal.setdefault(lit2, set()).add(i)
                    self.watched_literals_in_clause[i].add(lit2)

        if self.debug:
            print(f"clauses of watched lit: {self.clauses_of_watched_literal}")

        while self.bcp_queue: # while not_empty()
            unit_lit = self.bcp_queue.pop()
            if self.debug:
                print(f"popped: {unit_lit}")

            if abs(unit_lit) in self.assignment.keys(): # already assigned, skip
                # print("already assigned")
                continue
            else:
                self._assign_value(unit_lit, True)

            # clauses_indices = self.watched_literals[-unit_lit] 
            for i in list(self.clauses_of_watched_literal.get(-unit_lit, [])): # check clauses where lit is negated
                clause = self.clauses[i]
                
                # if a literal is set to True, and its negation is found in another unit clause,
                # this is a conflict
                if len(clause) == 1: 
                    self.bcp_queue = []
                    return False

                if self.debug:
                    print(f"clause: {clause} | without watched: {clause - self.watched_literals_in_clause[i]}")

                for lit in clause - self.watched_literals_in_clause[i]: # iterate over non-watched literals in clause
                   assigned = self.assignment.get(abs(lit)) # get assignment of current lit
                   if self.debug:
                        print(f"lit:{lit}")
                   if assigned is None or assigned == (lit > 0):# literal is unassigned or true
                        if i not in self.clauses_of_watched_literal[lit]: # literal is not watched by other watcher
                            #NOTE: move pointer to this literal

                            # here, we remove the current clause from from being a watching clause of -unit_lit,
                            # as we move it to another one because -unit_lit is false
                            self.clauses_of_watched_literal[-unit_lit].remove(i) 
                            self.clauses_of_watched_literal[lit].add(i)

                            # we remove -unit_lit as it cannot be watched
                            self.watched_literals_in_clause[i].remove(-unit_lit)
                            self.watched_literals_in_clause[i].add(lit)
                            break
                
                # After checking the whole clause
                if i in self.clauses_of_watched_literal[-unit_lit]: # if watch pointer was not moved
                    # the other watched literal is obtained by removing the current unit lit
                    # from the list of watched lits of the current clause
                    
                    # if empty, there is no other watched literal, hence bcp = false
                    if self.debug:
                        print(f"can be switched to {self.watched_literals_in_clause[i] - {-unit_lit}}")
                    if not self.watched_literals_in_clause[i] - {-unit_lit}:
                        return False

                    other_watched_literal = next(iter(self.watched_literals_in_clause[i] - {-unit_lit}))
                    if self.debug:
                        print(f"Other watched lit: {other_watched_literal}")

                    assigned = self.assignment.get(abs(other_watched_literal)) # get assignment of current lit
                    if assigned is None: # other lit not yet assigned, assign True and add to queue

                        # self.assign_value(other_watched_literal, True)
                        self.bcp_queue.append(other_watched_literal)
                    elif assigned == (other_watched_literal > 0): # other lit is true
                        continue
                    else:
                        self.bcp_queue = [] # Resets the bcp queue if conflict was derived
                        return False # conflict derived
        # if no conflict was derived
        return True

def simple_recursive(formula: Formula):
    if formula.clauses == []: # emtpy formula
        return True
    if set() in formula.clauses: # contains empty clause
        return False
    else:
        var = next(iter(formula.clauses[0])) #gets the first variable in the first clause
        return simple_recursive(formula.set_value_DEP(var)) or simple_recursive(formula.set_value_DEP(-var))



def simple_non_recursive(formula: Formula, debug = False):

    if formula.debug or debug:
        print(formula.clauses)

    decisions = []

    if formula.clauses == []:
        return True
    if set() in formula.clauses:
        return False

    # the assignment field of formula correspods to the decision stack
    if not formula.bcp(): # do first bcp
        return False
    elif not formula.open_assignments:
        return True
    
    decisions.append(0 + len(formula.assignment.keys())) # first decision level (index of first decision in trail), to ignore first bcp assignments
    val = True
    var = next(iter(formula.open_assignments))

    while formula.open_assignments: # not empty
        if formula.decide(var, val):

            #NOTE: next decision
            if not formula.open_assignments: # empty after bcp
                return True
            decisions.append(len(formula.assignment.keys()))
            var = next(iter(formula.open_assignments))
            val = True

        else:
            #NOTE: revert assignments until for this decision
            if len(decisions) == 0:
                return False
            start = decisions.pop()
            # TODO: check with proper timeout, then remove
            #
            # if start == -1:
            #     start = 0
            #
            assignments_to_revert = formula.trail[start:] # all assigments starting from last decision
            var_to_invert = assignments_to_revert[0]
            del formula.trail[start:] # removes them from the trail

            for lit in assignments_to_revert: # revert all assignments related to this decision
                formula.remove_assignment(lit)

            var = var_to_invert
            val = False

    return True





# run / testing

def test_bcp_watched_literals():
    # formula = parse_formula_from_file("test-formulas/f2r.in") #unit1, unit3
    formula = parse_formula_from_file("test-formulas/full3.in") #unit1, unit3
    # formula.debug = True
    print(f"Result: {simple_non_recursive(formula)}")

def test_recursive():
    folder = Path("test-formulas")
    recursion_error = 0
    succ = 0
    for file in folder.iterdir():
        print(file.resolve())
        formula = parse_formula_from_file(str(file.resolve()))
        try:
            print(simple_recursive(formula))
            succ += 1
        except RecursionError as e:
            print(e)
            recursion_error += 1
#

def main():
    parser = argparse.ArgumentParser(description="Use custom SAT-Solvers.")
    parser.add_argument(
        "--recursive", metavar="FILE", help="Use recursive solver to solve formula given in DIMACS."
    )
    parser.add_argument(
        "--non-recursive", metavar="FILE", help="Use recursive solver to solve formula given in DIMACS."
    )

    args = parser.parse_args()

    if args.recursive:
        result = simple_recursive(parse_formula_from_file(args.recursive))
        print(result)

    elif args.non_recursive:
        result = simple_non_recursive(parse_formula_from_file(args.non_recursive))
        print(result)
    else:
        print("Please use --recursive <path_to_file> or --non-recursive <path_to_file>.")





if __name__ == "__main__":
    main()
    # test_bcp_watched_literals()
    # formula = parse_formula_from_file("test-formulas/unit3.in")
    # print(simple_recursive(formula))









