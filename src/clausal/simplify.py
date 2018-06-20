"""
Module to simplify modal formula where possible.
Specifically, the module eliminates propositional constants and double negations from the input formula.
"""
import sys

import parser as p
import utilities as u


def simplify(ast_formula):
    """
    :param ast_formula: parsed expression represented as an abstract syntax tree (AST).
    :return: simplified formula represented as an AST.
    """
    try:
        return psimplfy(ast_formula)
    except Exception as e:
        print('Exception in simplifying the negated ast_formula: {}'.format(e.args[0]))


def psimplfy(ast_fml):
    if ast_fml and not isinstance(ast_fml, p.Atomic):
        connective = ast_fml[0]
        if not isinstance(connective, p.Atomic):
            switch = {
                '~': eval_not,
                '&': eval_and,
                '|': eval_or,
                '=>': eval_imp,
                '<=>': eval_iff,
                'box': eval_modality,
                'dia': eval_modality,
            }
            operation = switch.get(repr(connective), eval_error)
            return operation(ast_fml, connective)
        else:
            return connective
    else:
        return ast_fml


def eval_not(sub_fml, connective):
    left_fml = sub_fml[1]

    if left_fml == p.BOTTOM:
        return p.Atomic(p.TOP)
    elif left_fml == p.TOP:
        return p.Atomic(p.BOTTOM)
    elif not isinstance(left_fml, p.Atomic):
        if repr(left_fml[0]) == '~':
            return psimplfy(left_fml[1])
        else:
            return [connective, psimplfy(left_fml)]
    else:
        return sub_fml


def eval_and(sub_fml, connective):
    left_fml = sub_fml[1]
    right_fml = sub_fml[2]

    if left_fml == p.BOTTOM or right_fml == p.BOTTOM:
        return p.Atomic(p.BOTTOM)
    elif left_fml == p.TOP:
        return psimplfy(right_fml)
    elif right_fml == p.TOP:
        return psimplfy(left_fml)
    else:
        return [connective, psimplfy(left_fml), psimplfy(right_fml)]


def eval_or(sub_fml, connective):
    left_fml = sub_fml[1]
    right_fml = sub_fml[2]

    if left_fml == p.TOP or right_fml == p.TOP:
        return p.Atomic(p.TOP)
    elif left_fml == p.BOTTOM:
        return psimplfy(right_fml)
    elif right_fml == p.BOTTOM:
        return psimplfy(left_fml)
    else:
        return [connective, psimplfy(left_fml), psimplfy(right_fml)]


def eval_imp(sub_fml, connective):
    ant_fml = sub_fml[1]  # antecedent
    con_fml = sub_fml[2]  # consequent

    if ant_fml == p.BOTTOM or con_fml == p.TOP:
        return p.Atomic(p.TOP)
    elif ant_fml == p.TOP:
        return psimplfy(con_fml)
    elif con_fml == p.BOTTOM:
        return psimplfy([u.op('~'), ant_fml])
    else:
        return [connective, psimplfy(ant_fml), psimplfy(con_fml)]


def eval_iff(sub_fml, connective):
    left_fml = sub_fml[1]
    right_fml = sub_fml[2]

    if left_fml == p.TOP:
        return psimplfy(right_fml)
    elif right_fml == p.TOP:
        return psimplfy(left_fml)
    elif left_fml == p.BOTTOM:
        return psimplfy([u.op('~'), right_fml])
    elif right_fml == p.BOTTOM:
        return psimplfy([u.op('~'), left_fml])
    else:
        return [connective, psimplfy(left_fml), psimplfy(right_fml)]


def eval_modality(sub_fml, connective):
    left_fml = sub_fml[1]

    if not isinstance(left_fml, p.Atomic):
        return [connective, psimplfy(left_fml)]
    else:
        return sub_fml


def eval_error(sub_fml, connective):
    sys.stderr.write('Error in simplification: ' + str(sub_fml) + '\n')
    raise SystemExit(1)



