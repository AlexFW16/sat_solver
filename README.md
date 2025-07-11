# SAT Solvers
SAT Solvers for SAT-Solving Course at JKU.

Implemented a simple recursive solver and a non-recursive using BCP with watched literals solving formulas given in DIMACS.

Run `test.py --verify` to run the testing sricpt that checks for correctness via PySAT (timeout 5min).

Run `test.py --compare` to compare runtime & number of solved formulas (timeout 5min).

Run `main.py --recursive <path_to_file>` to use the recursive solver to solve a formula.

Run `main.py --non-recursive <path_to_file>` to use the non-recursive solver to solve a formula.
