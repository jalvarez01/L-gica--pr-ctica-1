# CNF Converter with Tseitin Encoding

#### Juan José Álvarez Ocampo

## System information

- **Operating System:** macOS Sequoia 15.6.1
- **Python Interpreter:** CPython 3.10.12
- **Development Environment:** Visual Studio Code 1.103.2
- **Runtime:** Python Virtual Machine (PVM)

## Running enstructions
### Prerequisites

- Python 3.8 or higher must be installed on your system
- No external dependencies required (uses only Python standard library)

#### Clone eepository
```bash

[git clone https://github.com/jalvarez01/L-gica--pr-ctica-1$0
cd cnf-converter](https://github.com/jalvarez01/L-gica--pr-ctica-2)

# Make executable (Unix/Linux/macOS)
chmod +x Formula.py

# Run the program
python3 Formula.py
```
## Detailed explanation of the solution

This implementation provides two algorithms for converting propositional logic to its CNF. The firts solution is a recursive descent parser that handles operator precedence and right-associativity for implication and equivalence operators, building an abstract syntax tree representation of the input formula. The standard CNF conversion follows the classical three-step pipeline: first eliminating implications (A → B becomes ¬A ∨ B) and equivalences (A ↔ B becomes (¬A ∨ B) ∧ (¬B ∨ A)), after that, it applies De Morgan's laws to push negations inward to literals only, and finally distributing disjunctions over conjunctions using the distributive law (A ∨ (B ∧ C) becomes (A ∨ B) ∧ (A ∨ C)). 

The Tseitin encoding implementation follows Algorithm 4.50: after preprocessing to eliminate implications/equivalences and apply NNF, it iteratively finds subformulae of the form (L ◦ R), where both L and R are literals, replaces each with a fresh variable pi, and adds CNF clauses encoding pi ↔ (L ◦ R) using specific patterns for conjunction and disjunction operators. This iterative process continues until the resulting formula is in CNF, producing an equisatisfiable formula with linear size growth.

## Reference sources

- Lecture Notes on Propositional Encodings, by: Matt Fredrikson
(https://www.cs.cmu.edu/~15414/s23/lectures/15-sat-encodings.pdf$0)

- Mathematical Logic for Computer Science, by: Mordechai Ben-Ari
