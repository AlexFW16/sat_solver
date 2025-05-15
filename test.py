import sys
from pathlib import Path
from pysat.formula import CNF
from pysat.solvers import Solver

# Adjust this import to point at where your solver code lives
from main import simple_non_recursive, parse_formula_from_file

def test_solver(solver_fn, name):
    """
    Test a custom solver function against PySAT's Solver.
    solver_fn: function taking a Formula object and returning True (SAT) or False (UNSAT).
    name: descriptive name for the solver.
    """
    test_dir = Path("test-formulas")
    # test_dir = Path("temp-test")
    total = correct = 0

    for file in sorted(test_dir.iterdir()):
        if not file.is_file():
            continue
        total += 1

        # 1) Load with PySAT
        cnf = CNF(from_file=str(file))
        with Solver(name="glucose3", bootstrap_with=cnf.clauses) as pysat_solver:
            pysat_res = pysat_solver.solve()

        # 2) Load with your parser & solver
        formula = parse_formula_from_file(str(file))
        custom_res = solver_fn(formula)

        ok = (custom_res == pysat_res)
        status = "OK" if ok else "WRONG"
        if ok:
            correct += 1

        print(f"{file.name:30}  {name:22}  custom={custom_res:<5}  pysat={pysat_res:<5}  [{status}]")

    print(f"\n{name}: {correct}/{total} correct\n")


def main():

    print("\n=== Non-Recursive Watched-Literals BCP Solver ===")
    test_solver(simple_non_recursive, "simple_non_recursive")


if __name__ == "__main__":
    main()

