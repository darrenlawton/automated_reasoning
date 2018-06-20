import time
import argparse


from clausal.clausifer import transform
from prover.k_prove import *
from z3 import sat


def prove(formula, verbose):
    """
    :param formula: String representation of a modal formula.
    The syntax for such a formula is per the grammar as stipulated in the README.
    Example input: "(a|b) & (~c => d)"

    :return string showing the outcome of the proof, that is valid or not valid.
    """
    try:
        sys.setrecursionlimit(15000)
        negated_fml = "~(" + str(formula) + ")"

        negated_clausal_fml = call_function(verbose, transform, negated_fml, False)

        if call_function(verbose, k_prove, negated_clausal_fml) == sat:
            return "Psi is NOT valid"
        else:
            return "Psi is valid"

    finally:
        sys.setrecursionlimit(1000)


def call_function(verbose, function, *args):
    if verbose: return timed(function, *args)
    else: return function(*args)


def timed(function, *args):
    start = time.time()
    result = function(*args)
    end = time.time()

    print(str(function.__name__) + " was completed in " +  str(end-start) + " s.")
    return result


if __name__ == '__main__':
    if sys.version_info[0] < 3:
        expr = raw_input("")
    else: expr = input("")

    parser = argparse.ArgumentParser(description="Please consult the README for help.")
    parser.add_argument('-v', action='store_true')

    args = parser.parse_args()
    if expr:
        print(prove(expr, args.v))

