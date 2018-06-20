# SATtab
A SAT-Based Theorem Prover for Modal Logic K.

### Prerequisites
To run this software you will need to install the ply and z3-solver packages.
Depending on your Python version, these packages can be installed using the following commands:
	* pip3 install ply 
	* pip3 install z3-solver 

### Using the software
Usage: python3 src/main.py [-v] 

The prover will read one line of standard input as a modal logic formula, and
will return whether this formula is provable or not. That is, it will negate
the input formula, and test whether this negation is satisfiable.

There are several further options:
-v		Output verbose basic statistics about the internal workings of the program.

The prover accepts formulae in the following syntax:

fml ::= '(' fml ')'      	       ( parentheses )
	| 'True'                       ( truth )
	| 'False'                      ( falsehood )
	| '~' fml	               ( negation )
	| '<' id '>' fml | '<>' fml    ( diamonds )
	| '[' id ']' fml | '[]' fml    ( boxes )
	| fml '&' fml                  ( conjunction )
	| fml '|' fml                  ( disjunction )
	| fml '=>' fml                 ( implication )
	| fml '<=>' fml                ( equivalence )
	| id                           ( classical literals )

where identifiers (id) are arbitrary nonempty alphanumeric sequences
(['A'-'Z' 'a'-'z' '0'-'9']+)

## Running the benchmarks
There are several benchmark sets that are available in the 'benchmarks' folder. The problem files ending with .k are located within each subfolder and are represented in the correct syntax. 

A benchmark testing script can be run as following:
	* python3 src/prover/testing/testing_prover.py

## Authors

* **Darren Lawton**

## License

This project is licensed under the MIT License

## Acknowledgments

* Professor Rajeev Gore
