from pathlib import Path
    
def parse_formula_from_file(file_path: str):
    lines = ""
    with open(file_path) as file:
        lines = "\n".join(line.rstrip() for line in file)
    return parse_formula_from_string(lines)

def parse_formula_from_string(content: str):
    
    lines = content.split("\n")
    (num_vars, num_clauses) = lines[0].split(" ")[2:]

    formula = [set(map(int, clause.strip().split())) - {0} for clause in lines[1:]]
    return Formula(int(num_vars), int(num_clauses), formula)

# clauses only conain not-yet assigned variables
# history is stores stack of previous versions of clauses
# check set() in clauses to check for empty clause = bottom, and clauses = [] for top
class Formula():
    
    def __init__(self,num_vars: int, num_clauses: int, clauses: list[set], debug: bool =False):
        self.num_vars = num_vars
        self.num_clauses = num_clauses
        self.clauses = clauses # current clauses
        self.history = [] # previous clauses
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
    # NOTE: does not update num_vars and num_clauses (yet)
    #FIX: Deprecated
    def set_value_DEP(self, var: int):
        self.assignment[abs(var)] = True if var > 0 else False
        self.history.append(self.clauses)
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
        self.clauses = new_clauses
        return self

    # returns false if already assigned, but DOES NOT overwrite
    def assign_value(self, var: int, value: bool): 
        if abs(var) in self.assignment.keys():
            if self.debug:
                print(f"Assignment {var} : {self.assignment[abs(var)]} already exists")
            return False
        else:
            self.open_assignments.remove(abs(var)) # stores the literal as assigned

        self.assignment[abs(var)] = value if var > 0 else (not value) # store truth value
        self.trail.append(abs(var))  # store in assignment trail

        self.bcp_queue.append(-var if value else var)

        return True

    def remove_assignment(self, var: int):
        if abs(var) not in self.assignment.keys():
            if self.debug:
                print(f"Variable {var} is not assigned yet.")
            return False
        del self.assignment[var]
        self.open_assignments.add(abs(var))
        return True

        

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
                        #TODO: Find out why it breaks when I do this? Should be correct
                        self.assign_value(lit1, True)
                        # self.bcp_queue.append(-lit1)
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
            self.assign_value(unit_lit, unit_lit > 0)

            # clauses_indices = self.watched_literals[-unit_lit] 
            for i in list(self.clauses_of_watched_literal.get(unit_lit, [])): # check clauses where lit is negated
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
                            #TODO: move pointer to this literal
                            self.clauses_of_watched_literal[unit_lit].remove(i)
                            self.clauses_of_watched_literal[lit].add(i)

                            self.watched_literals_in_clause[i].remove(unit_lit)
                            self.watched_literals_in_clause[i].add(lit)
                            break
                
                # After checking the whole clause
                if i in self.clauses_of_watched_literal[unit_lit]: # if watch pointer was not moved
                    # the other watched literal is obtained by removing the current unit lit
                    # from the list of watched lits of the current clause
                    other_watched_literal = next(iter(self.watched_literals_in_clause[i] - {unit_lit}))

                    assigned = self.assignment.get(abs(other_watched_literal)) # get assignment of current lit
                    if assigned is None: # other lit not yet assigned, assign True and add to queue
                        self.assign_value(other_watched_literal, True)
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
        #TODO: Fix
        # return simple_recursive(formula.set_value(var)) or simple_recursive(formula.set_value(-var))


def simple_non_recursive(formula: Formula):
    # optimisation
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

    # make first decision
    var = next(iter(formula.open_assignments))
    decisions.append(0 + len(formula.assignment.keys())) # first decision level (index of first decision in trail), to ignore first bcp assignments
    formula.assign_value(var, True)

    while formula.open_assignments: # not empty
        if formula.bcp():
            #NOTE: next decision
            if not formula.open_assignments: # empty after bcp
                return True
            var = next(iter(formula.open_assignments))
            formula.assign_value(var, True)
            decisions.append(len(formula.assignment.keys()))

        else:
            #NOTE: revert assignments until for this decision
            if len(decisions) == 0:
                return False
            start = decisions.pop() -1 # to also include the variable to invert (last decision)

            if start == -1:
                start = 0

            assignments_to_revert = formula.trail[start:] # all assigments starting from last decision
            var_to_invert = assignments_to_revert[0]
            del formula.trail[start:] # removes them from the trail

            for lit in assignments_to_revert: # revert all assignments related to this decision
                formula.remove_assignment(lit)
            formula.assign_value(var_to_invert, False) # inverts the last value to invert the decision
    return True





    
    



# run / testing

def test_bcp_watched_literals():
    formula = parse_formula_from_file("test-formulas/unit1.in")
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

test_bcp_watched_literals()









