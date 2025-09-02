from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Union, Optional


class OpType(Enum):
    EQUIV = 1    # <->
    IMPL = 2     # ->
    OR = 3       # v
    AND = 4      # &
    NOT = 5      # -


@dataclass
class Formula:
    op: Union[OpType, str]          
    left: Optional['Formula'] = None
    right: Optional['Formula'] = None

    def is_variable(self) -> bool:
        return isinstance(self.op, str)

    def is_literal(self) -> bool:
        return self.is_variable() or (self.op == OpType.NOT and self.left and self.left.is_variable())

    def __str__(self) -> str:
        if self.is_variable():
            return self.op
        if self.op == OpType.NOT:
            return f"-{self.left}"
        sym = {OpType.AND:'&', OpType.OR:'v', OpType.IMPL:'->', OpType.EQUIV:'<->'}
        return f"({self.left} {sym[self.op]} {self.right})"

class FormulaParser:
    def __init__(self, s: str):
        self.tokens = self._tokenize(s)
        self.pos = 0

    def _tokenize(self, s: str) -> List[str]:
        s = s.replace(' ', '')
        out, i = [], 0
        while i < len(s):
            if s[i:i+3] == '<->': out.append('<->'); i += 3
            elif s[i:i+2] == '->': out.append('->'); i += 2
            elif s[i] in '-&v()': out.append(s[i]); i += 1
            elif s[i].isalnum() or s[i] == '_':
                j = i
                while j < len(s) and (s[j].isalnum() or s[j] == '_'): j += 1
                out.append(s[i:j]); i = j
            else:
                i += 1
        return out

    def parse(self) -> Formula:
        node = self._parse_equiv()
        if self.pos != len(self.tokens):
            raise ValueError(f"Extraneous input at {self.tokens[self.pos]!r}")
        return node

    def _parse_equiv(self) -> Formula:
        left = self._parse_impl()
        if self.pos < len(self.tokens) and self.tokens[self.pos] == '<->':
            self.pos += 1
            right = self._parse_equiv()  
            return Formula(OpType.EQUIV, left, right)
        return left

    def _parse_impl(self) -> Formula:
        left = self._parse_or()
        if self.pos < len(self.tokens) and self.tokens[self.pos] == '->':
            self.pos += 1
            right = self._parse_impl()   
            return Formula(OpType.IMPL, left, right)
        return left

    def _parse_or(self) -> Formula:
        left = self._parse_and()
        while self.pos < len(self.tokens) and self.tokens[self.pos] == 'v':
            self.pos += 1
            right = self._parse_and()
            left = Formula(OpType.OR, left, right)
        return left

    def _parse_and(self) -> Formula:
        left = self._parse_not()
        while self.pos < len(self.tokens) and self.tokens[self.pos] == '&':
            self.pos += 1
            right = self._parse_not()
            left = Formula(OpType.AND, left, right)
        return left

    def _parse_not(self) -> Formula:
        if self.pos < len(self.tokens) and self.tokens[self.pos] == '-':
            self.pos += 1
            return Formula(OpType.NOT, self._parse_not())
        return self._parse_primary()

    def _parse_primary(self) -> Formula:
        if self.pos < len(self.tokens) and self.tokens[self.pos] == '(':
            self.pos += 1
            node = self._parse_equiv()
            if self.pos >= len(self.tokens) or self.tokens[self.pos] != ')':
                raise ValueError("Expected ')'")
            self.pos += 1
            return node
        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]; self.pos += 1
            return Formula(tok)
        raise ValueError("Unexpected end")

class CNFConverter:
    def __init__(self):
        pass

    def _elim_equiv_impl(self, f: Formula) -> Formula:
        if f.is_variable(): return f
        if f.op == OpType.NOT:
            return Formula(OpType.NOT, self._elim_equiv_impl(f.left))
        A = self._elim_equiv_impl(f.left) if f.left else None
        B = self._elim_equiv_impl(f.right) if f.right else None
        if f.op == OpType.IMPL:
            return Formula(OpType.OR, Formula(OpType.NOT, A), B)
        if f.op == OpType.EQUIV:
            l = Formula(OpType.OR, Formula(OpType.NOT, A), B)
            r = Formula(OpType.OR, Formula(OpType.NOT, B), A)
            return Formula(OpType.AND, l, r)
        if f.op in (OpType.AND, OpType.OR):
            return Formula(f.op, A, B)
        return f

    def _nnf(self, f: Formula) -> Formula:
        if f.is_variable(): return f
        if f.op == OpType.NOT:
            g = f.left
            if g.is_variable(): return f
            if g.op == OpType.NOT: return self._nnf(g.left)
            if g.op == OpType.AND:
                return self._nnf(Formula(OpType.OR, Formula(OpType.NOT, g.left), Formula(OpType.NOT, g.right)))
            if g.op == OpType.OR:
                return self._nnf(Formula(OpType.AND, Formula(OpType.NOT, g.left), Formula(OpType.NOT, g.right)))
        if f.right is None:
            return Formula(f.op, self._nnf(f.left))
        return Formula(f.op, self._nnf(f.left), self._nnf(f.right))

    def _dist_or_over_and(self, f: Formula) -> Formula:
        if f.is_variable() or f.is_literal(): return f
        if f.op == OpType.NOT: return Formula(OpType.NOT, self._dist_or_over_and(f.left))
        L = self._dist_or_over_and(f.left) if f.left else None
        R = self._dist_or_over_and(f.right) if f.right else None
        if f.op == OpType.AND: return Formula(OpType.AND, L, R)
        if f.op == OpType.OR:  return self._dist(L, R)
        return Formula(f.op, L, R)

    def _dist(self, A: Formula, B: Formula) -> Formula:
        if A.op == OpType.AND:
            return Formula(OpType.AND, self._dist(A.left, B), self._dist(A.right, B))
        if B.op == OpType.AND:
            return Formula(OpType.AND, self._dist(A, B.left), self._dist(A, B.right))
        return Formula(OpType.OR, A, B)

    def to_cnf_equiv(self, f: Formula) -> List[List[str]]:
        f1 = self._elim_equiv_impl(f)
        f2 = self._nnf(f1)
        f3 = self._dist_or_over_and(f2)
        return self._formula_to_clauses(f3)

    def _formula_to_clauses(self, f: Formula) -> List[List[str]]:
        if f.op == OpType.AND:
            return self._formula_to_clauses(f.left) + self._formula_to_clauses(f.right)
        return [self._or_to_literals(f)]

    def _or_to_literals(self, f: Formula) -> List[str]:
        if f.op == OpType.OR:
            return self._or_to_literals(f.left) + self._or_to_literals(f.right)
        if f.is_variable(): return [f.op]
        if f.op == OpType.NOT and f.left.is_variable(): return [f"-{f.left.op}"]
        return [str(f)]  # fallback

    def _is_clause(self, f: Formula) -> bool:
        if f.is_literal(): return True
        if f.op == OpType.OR: return self._is_clause(f.left) and self._is_clause(f.right)
        return False

    def _is_cnf(self, f: Formula) -> bool:
        if f.is_literal(): return True
        if f.op == OpType.AND: return self._is_cnf(f.left) and self._is_cnf(f.right)
        if f.op == OpType.OR:  return self._is_clause(f.left) and self._is_clause(f.right)
        return False

    def tseitin_450(self, f: Formula) -> List[List[str]]:
        
        g = self._elim_equiv_impl(f)
        g = self._nnf(g)

        clauses: List[List[str]] = []
        fresh_id = 0

        def fresh() -> str:
            nonlocal fresh_id
            fresh_id += 1
            return f"t{fresh_id}"

        def lit_to_str(x: Formula) -> str:
            if x.is_variable(): return x.op
            if x.op == OpType.NOT and x.left.is_variable(): return f"-{x.left.op}"
            raise ValueError("Expected literal")

        def negate(s: str) -> str:
            return s[1:] if s.startswith('-') else f"-{s}"

        def add_equiv_cnf(p: str, op: OpType, L: str, R: str):
            if op == OpType.AND:
                
                clauses.append([f"-{p}", L])
                clauses.append([f"-{p}", R])
                clauses.append([negate(L), negate(R), p])
            elif op == OpType.OR:
                
                clauses.append([p, negate(L)])
                clauses.append([p, negate(R)])
                clauses.append([f"-{p}", L, R])
            else:
                
                raise ValueError("Only AND/OR expected here")

        def find_literal_binary(h: Formula, path: List[str]) -> Tuple[Optional[Formula], List[str]]:
            if h.is_variable() or h.op == OpType.NOT:
                
                if h.op == OpType.NOT:
                    return find_literal_binary(h.left, path + ['left'])
                return None, []
            
            if h.left and h.right:
                if h.op in (OpType.AND, OpType.OR) and h.left.is_literal() and h.right.is_literal():
                    return h, path
                
                res, pth = find_literal_binary(h.left, path + ['left'])
                if res is not None: return res, pth
                res, pth = find_literal_binary(h.right, path + ['right'])
                if res is not None: return res, pth
            return None, []

        def replace_at(h: Formula, path: List[str], atom: Formula) -> Formula:
            if not path: return atom
            d, rest = path[0], path[1:]
            if d == 'left':
                return Formula(h.op, replace_at(h.left, rest, atom), h.right)
            else:
                return Formula(h.op, h.left, replace_at(h.right, rest, atom))

        while not self._is_cnf(g):
            node, path = find_literal_binary(g, [])
            if node is None:
                
                break

            Ls, Rs = lit_to_str(node.left), lit_to_str(node.right)
            p = fresh()
            add_equiv_cnf(p, node.op, Ls, Rs)
            g = replace_at(g, path, Formula(p))

        cnf_g = self._formula_to_clauses(g) if self._is_cnf(g) else self.to_cnf_equiv(g)
        return self._dedup_simplify(clauses + cnf_g)

    def _dedup_simplify(self, cls: List[List[str]]) -> List[List[str]]:
        
        norm: List[List[str]] = []
        for c in cls:
            s = set(c)
            if any(l.startswith('-') and l[1:] in s for l in s) or any(('-'+l) in s for l in s if not l.startswith('-')):
                continue
            norm.append(sorted(s))
        out: List[List[str]] = []
        for i, c in enumerate(norm):
            sc = set(c)
            if any(set(d).issubset(sc) and set(d) != sc for j, d in enumerate(norm) if i != j):
                continue
            out.append(c)
        return out

def format_cnf(clauses: List[List[str]]) -> str:
    if not clauses: return "TRUE"
    parts = []
    for cl in clauses:
        parts.append(cl[0] if len(cl)==1 else "(" + " v ".join(cl) + ")")
    return " & ".join(parts)

def main():
    import sys
    
    arg = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    conv = CNFConverter()

    def run_once(s: str):
        parser = FormulaParser(s)
        f = parser.parse()
        print(f"\nParsed: {f}")
        mode = input("Use (s)tandard CNF or Tseitin (t)? [s/t]: ").strip().lower()
        if mode == 't':
            clauses = conv.tseitin_450(f)
            print(f"Tseitin CNF: {format_cnf(clauses)}")
        else:
            clauses = conv.to_cnf_equiv(f)
            print(f"Standard CNF: {format_cnf(clauses)}")
        print(f"Clauses: {len(clauses)}")

    if arg:
        try:
            parser = FormulaParser(arg)
            f = parser.parse()
            print(f"Parsed: {f}")
            
            cnf_eq = conv.to_cnf_equiv(f)
            print("\n[Equivalent CNF]")
            print(format_cnf(cnf_eq), f"\n#clauses={len(cnf_eq)}")
            tseitin = conv.tseitin_450(f)
            print("\n[Tseitin]")
            print(format_cnf(tseitin), f"\n#clauses={len(tseitin)}")
        except Exception as e:
            print("Error:", e)
        return

    print("Interactive Mode (type 'quit' to exit)")
    while True:
        try:
            s = input("\nEnter formula: ").strip()
            if s.lower() == 'quit': break
            if not s: continue
            run_once(s)
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
