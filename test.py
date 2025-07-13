import concurrent.futures
import argparse
from pathlib import Path
from pysat.formula import CNF
from pysat.solvers import Solver
from main import simple_non_recursive, parse_formula_from_file, simple_recursive
import time

TEST_DIR = Path("test-formulas")
FILES = sorted(
    (p for p in TEST_DIR.iterdir() if p.is_file()), key=lambda p: p.stat().st_size
)


# Necessary to get unique timings on simultaneously exectuted threads
def timed_solver_call(solver_fn, formula):
    start = time.perf_counter()
    res = solver_fn(formula)
    duration = time.perf_counter() - start
    return res, duration


def test_solver(solver_fn, name, timeout=60):
    total = correct = timeouts = 0

    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        for file in FILES:
            total += 1

            # PySAT baseline
            cnf = CNF(from_file=str(file))
            with Solver(name="glucose3", bootstrap_with=cnf.clauses) as pysat_solver:
                pysat_res = pysat_solver.solve()

            # custom solver
            print(f"Solving {file.name:30}…")
            formula = parse_formula_from_file(str(file))
            future = pool.submit(solver_fn, formula)

            try:
                custom_res = future.result(timeout=timeout)
                status = "OK" if custom_res == pysat_res else "WRONG"
                if custom_res == pysat_res:
                    correct += 1
            except concurrent.futures.TimeoutError:
                status = "TIMEOUT"
                custom_res = None
                timeouts += 1
                future.cancel()
            except Exception as e:
                status = f"ERROR ({e.with_traceback})"
                custom_res = None

            print(
                f"{file.name:30}  {name:22}  custom={str(custom_res):<5}  pysat={pysat_res:<5}  [{status}]"
            )
        # makes sure the overview below is actually printed
        pool.shutdown(wait=False, cancel_futures=True)

    print(
        f"\n{name}: {correct}/{total - timeouts} correct and {timeouts} timeouts (Overall: {total})\n"
    )


# compares two solvers, does not consider correctness of results
def compare_solvers(solver_fn1, name1, solver_fn2, name2, timeout=300):
    total = timeouts1 = timeouts2 = 0
    sum_time1 = sum_time2 = 0

    with concurrent.futures.ProcessPoolExecutor() as pool:
        for file in FILES:
            total += 1

            status1 = status2 = "OK"
            elapsed1 = elapsed2 = None

            formula = parse_formula_from_file(str(file))

            future1 = pool.submit(
                timed_solver_call, solver_fn1, formula
            )  # executes the method in its own thread
            future2 = pool.submit(
                timed_solver_call, solver_fn2, formula
            )  # executes the method in its own thread

            try:
                _, elapsed1 = future1.result(timeout=timeout)
                sum_time1 += elapsed1
            except concurrent.futures.TimeoutError:
                future1.cancel()
                status1 = "TIMEOUT"
                timeouts1 += 1

            except Exception:
                future1.cancel()
                status1 = f"ERROR"
                timeouts1 += 1

            try:
                _, elapsed2 = future2.result(timeout=timeout)
                sum_time2 += elapsed2
            except concurrent.futures.TimeoutError:
                future2.cancel()
                status2 = "TIMEOUT"
                timeouts2 += 1
            except Exception:
                future2.cancel()
                status2 = f"ERROR"
                timeouts2 += 1

            time_1 = f"{elapsed1:.2f}s" if elapsed1 is not None else "--"
            time_2 = f"{elapsed2:.2f}s" if elapsed2 is not None else "--"

            print(
                f"{file.name:30}  {name1}={str(time_1):<5} [{status1}] | {name2}={time_2:<5} [{status2}]"
            )

        # makes sure the overview below is actually printed
        pool.shutdown(wait=False, cancel_futures=True)

    avg_time_1 = sum_time1 / (total - timeouts1)
    avg_time_2 = sum_time2 / (total - timeouts2)
    print(
        f"\n{name1}: Average solving time: {avg_time_1:.5f}, Number of timeouts/errors: {timeouts1} (out of {total})"
    )
    print(
        f"\n{name2}: Average solving time: {avg_time_2:.5f}, Number of timeouts/errors: {timeouts2} (out of {total})"
    )
    exit(0)


def main():
    parser = argparse.ArgumentParser(description="Test custom SAT solvers.")
    parser.add_argument(
        "--verify-recursive", action="store_true", help="Verify correctness against PySAT."
    )
    parser.add_argument(
        "--verify-non-recursive", action="store_true", help="Verify correctness against PySAT."
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare runtime and number of solved instances for 5min timeout.",
    )

    args = parser.parse_args()

    if args.verify_recursive:
        print("\nRecursive with 1min timeout")
        test_solver(simple_recursive, "simple_recursive", timeout=1)

    elif args.verify_non_recursive:
        print("\nNon-Recursive using watched literal BCP with 1min timeout")
        test_solver(simple_non_recursive, "simple_non_recursive", timeout=5)
        print("here")
    elif args.compare:
        print("\n=== Comparing ===")
        compare_solvers(
            simple_recursive,
            "simple_recursive",
            simple_non_recursive,
            "simple_non_recursive",
            timeout=5,
        )
    else:
        print("Please use --verify-recursive, --verify_non_recursive or --compare.")


if __name__ == "__main__":
    main()
    exit(0)
