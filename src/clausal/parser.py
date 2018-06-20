import sys
from ply import *

TOP = 'True'
BOTTOM = 'False'


# Define classes for required operators - atomic, modalities and operators
class Atomic(object):
    def __init__(self, atom):
        self.atom = atom

    def __str__(self):
        return str(self.atom)

    def __eq__(self, other):
        if str(self.atom) == str(other):
            return True
        else:
            return False

    def __hash__(self):
        return hash(str(self.atom))

    __repr__ = __str__


class Modality(object):
    def __init__(self, mode, m_id):
        self.mode = mode
        self.id = m_id

    def __repr__(self):
        return str(self.mode)

    def __str__(self):
        if self.mode == "box":
            return "[" + self.id + "]"
        elif self.mode == "dia":
            return "<" + self.id + ">"

    def __eq__(self, other):
        if isinstance(self, Modality) and isinstance(other, Modality):
            if str(self.mode) == str(other.mode) and self.id == other.id:
                return True
        else:
            return False

    def __hash__(self):
        return hash(self.mode) + hash(self.id)


class Operator(object):
    def __init__(self, mode):
        self.mode = mode

    def __str__(self):
        return str(self.mode)

    __repr__ = __str__


# Get the token mapping from lexer.
from lexer import tokens

# Define a BNF grammar for modal logic.
'''
formula0 : 'false'
       | 'true'
       | term
       | '~' formula1
       | '(' formula1 ')'
       | '[id]' formula1
       | '<id>' formula1
       | formula1 '=>' formula1      # right associative
     | formula1 '|' formula1       # left associative
     | formula1 '&' formula1       # left associative
term0    : ATOM
'''

# Define token preference, from lowest to highest.
precedence = (
    ('right', 'IMP', 'IFF'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'BOX', 'DIA', 'NOT'),
)


def p_formula_braced(p):
    """
      formula : LPAREN formula RPAREN
      """
    p[0] = p[2]


def p_formula_modal(p):
    """
      formula : BOX formula
        | DIA formula
      """
    if p[1][:1] == '[':
        syn = 'box'
    elif p[1][:1] == '<':
        syn = 'dia'
    else:
        pass

    m_id = p[1][1:-1]

    p[0] = [Modality(syn, m_id), p[2]]


def p_formula_not(p):
    """
      formula : NOT formula
      """
    p[0] = [Operator(p[1]), p[2]]


def p_formula_binary(p):
    """
      formula : formula IMP formula
        | formula IFF formula
        | formula AND formula
        | formula OR formula
      """
    p[0] = [Operator(p[2]), p[1], p[3]]


def p_formula_atomic(p):
    """
      formula : false
        | true
        | term
      """
    global TOP, BOTTOM

    if str(p[1]).lower() == 'true':
        p[0] = Atomic(TOP)
    elif str(p[1]).lower() == 'false':
        p[0] = Atomic(BOTTOM)
    else:
        p[0] = p[1]


def p_term_atom(p):
    """
    term : ATOM
    """
    p[0] = Atomic(p[1])


# Error rule for syntax errors
def p_error(p):
    sys.stderr.write('Syntax error in input. \n')
    raise SystemExit(1)


bparser = yacc.yacc()


def parse(data, debug=0):
    bparser.error = 0
    p = bparser.parse(data, debug=debug)
    if bparser.error:
        return None
    return p
