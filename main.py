def parse_formula_from_file(file_path: str):
    lines = ""
    with open(file_path) as file:
        for line in file:
            lines += line
    return parse_formula_from_string(lines)

def parse_formula_from_string(content: str):
    lines = content.split("\n")
    (num_vars, num_clauses) = lines[0].split(" ")[2:]

    formula = [set(map(int, clause.strip().split())) - {0} for clause in lines[1:-1]]
    return (num_vars, num_clauses, formula)

# clauses only conain not-yet assigned variables
# history is stores stack of previous versions of clauses
# check set() in clauses to check for empty clause = bottom, and clauses = [] for top
class Formula():
    
    def __init__(self,num_vars, num_clauses, clauses: list[set]):
        self.num_vars = num_vars
        self.num_clauses = num_clauses
        self.clauses = clauses # current clauses
        self.history = [] # previous clauses

    def __str__(self):
        return "[" + ", ".join(["{" + " ".join(map(str, clause)) + "}" for clause in self.clauses]) + "]"

    # use e.g. -3 to set x3 to false
    def set_value(self, var: int):
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
        return new_clauses




def simple_recursive(formula: list[list]):
    if formula == []:
        return True
    if [] in formula:
        return False
    else:
        var = "x"




# run / testing
formula = Formula(*parse_formula_from_file("test.ln"))
formula.set_value(-5)
formula.set_value(-1)
# formula.set_value(-2)
# formula.set_value(-6)
print(formula)













