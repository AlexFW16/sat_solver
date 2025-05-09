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
    return Formula(num_vars, num_clauses, formula)

# clauses only conain not-yet assigned variables
# history is stores stack of previous versions of clauses
# check set() in clauses to check for empty clause = bottom, and clauses = [] for top
class Formula():
    
    def __init__(self,num_vars, num_clauses, clauses: list[set]):
        self.num_vars = num_vars
        self.num_clauses = num_clauses
        self.clauses = clauses # current clauses
        self.history = [] # previous clauses
        self.assignment = {}

    def __str__(self):
        return "Clauses: [" + ", ".join(["{" + " ".join(map(str, clause)) + "}" for clause in self.clauses]) + "] \n" \
            + "Assignment: [" +  " ,".join(f"{var}={value}" for (var, value) in self.assignment.items())  + "]"

    # use e.g. -3 to set x3 to false
    # NOTE: does not update num_vars and num_clauses (yet)
    def set_value(self, var: int):
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



def simple_recursive(formula: Formula):
    if formula.clauses == []: # emtpy formula
        return True
    if set() in formula.clauses: # contains empty clause
        return False
    else:
        var = next(iter(formula.clauses[0])) #gets the first variable in the first clause
        return simple_recursive(formula.set_value(var)) or simple_recursive(formula.set_value(-var))




# run / testing

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

print(f"Recursion Errors: {recursion_error} | Successful: {succ}")









