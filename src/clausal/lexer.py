"""
Module contains lexing rules for modal logic
"""
from ply import *


class Atomic(object):
    def __init__(self, atom):
        self.atom = atom


# Reserved words
reserved = {
    'True': 'true',
    'False': 'false',
}

# List of token names.
tokens = [
             'LPAREN',
             'RPAREN',
             'BOX',
             'DIA',
             'ATOM',
             'NOT',
             'AND',
             'OR',
             'IMP',
             'IFF',
         ] + list(reserved.values())

# Regular expression rules for simple tokens
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_BOX = r'\[' + '[a-zA-Z_0-9]*?' + '\]'
t_DIA = r'\<' + '[a-zA-Z_0-9]*?' + '\>'
t_NOT = r'\~'
t_AND = r'\&'
t_OR = r'\|'
t_IMP = r'\=>'
t_IFF = r'\<=>'


def t_ATOM(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ATOM')
    return t


# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t "'


# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lex.lex(debug=0)
