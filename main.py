def parse_formula_from_file(file_path: str):
    lines = ""
    with open(file_path) as file:
        for line in file:
            lines += line
    return parse_formula_from_string(lines)

def parse_formula_from_string(content: str):
    lines = content.split("\n")
    (vars, clauses) = lines[0].split(" ")[2:]

    # clauses = [clause[0:-1].strip().split(" ") for clause in lines[1:-1]] 

    formula = [list(map(int, clause.strip().split()))[:-1] for clause in lines[1:-1]]
    return formula





# run / testing
parse_formula_from_file("test.ln")

