"""
Module to convert a parsed formula into negation normal form.
"""
import sys


import parser
import simplify
import utilities as u


def to_nnf(ast_formula):
    """
    :param ast_formula: parsed expression represented as an abstract syntax tree (AST).
    :return: simplified formula represented as an AST.
    """
    try:
        return nenf(ast_formula)
    except Exception as e:
        print('Exception in negation normal forming ast_formula: {}'.format(e.args[0]))


def nenf(ast_fml):
    if ast_fml and not isinstance(ast_fml, parser.Atomic):
        connective = ast_fml[0]
        if not isinstance(connective, parser.Atomic):
            switch = {
                '~': nnf_not,
                '=>': nnf_imp,
                '<=>': nnf_iff,
                '&': nnf_binary,
                '|': nnf_binary,
                'box': nnf_modality,
                'dia': nnf_modality,
            }
            operation = switch.get(repr(connective), nnf_error)
            return operation(ast_fml, connective)
        else:
            return connective
    else:
        return ast_fml


def nnf_not(sub_fml, connective):
    left_fml = sub_fml[1]

    if not isinstance(left_fml, parser.Atomic):
        left_con = left_fml[0]
        if repr(left_con) == '~':
            return nenf(left_fml[1])
        elif repr(left_con) == '&':
            return [u.op('|'), nenf([u.op('~'), left_fml[1]]), nenf([u.op('~'), left_fml[2]])]
        elif repr(left_con) == '|':
            return [u.op('&'), nenf([u.op('~'), left_fml[1]]), nenf([u.op('~'), left_fml[2]])]
        elif repr(left_con) == '=>':
            return [u.op('&'), nenf(left_fml[1]), nenf([u.op('~'), left_fml[2]])]
        elif repr(left_con) == '<=>':
            return [u.op('|'), [u.op('&'), nenf(left_fml[1]), nenf([u.op('~'), left_fml[2]])],
                    [u.op('&'), nenf([u.op('~'), left_fml[1]]), nenf(left_fml[2])]]
        elif repr(left_con) == 'box':
            # Transfer relation id to modality
            return [parser.Modality('dia', left_con.id), nenf([u.op('~'), left_fml[1]])]
        elif repr(left_con) == 'dia':
            # Transfer relation id to modality
            return [parser.Modality('box', left_con.id), nenf([u.op('~'), left_fml[1]])]
        else:
            return [connective, nenf(left_fml)]
    else:
        return sub_fml


def nnf_binary(sub_fml, connective):
    left_fml = sub_fml[1]
    right_fml = sub_fml[2]

    return [connective, nenf(left_fml), nenf(right_fml)]


def nnf_imp(sub_fml, con):
    """ eliminate implications """
    ant_fml = sub_fml[1]  # antecedent
    con_fml = sub_fml[2]  # consequent

    return [u.op('|'), nenf([u.op('~'), ant_fml]), nenf(con_fml)]


def nnf_iff(sub_fml, connective):
    """ eliminate if and only ifs """
    left_fml = sub_fml[1]
    right_fml = sub_fml[2]

    return [u.op('|'), [u.op('&'), nenf(left_fml), nenf(right_fml)],
            [u.op('&'), nenf([u.op('~'), left_fml]), nenf([u.op('~'), right_fml])]]


def nnf_modality(sub_fml, connective):
    left_fml = sub_fml[1]

    if not isinstance(left_fml, parser.Atomic):
        return [connective, nenf(left_fml)]
    else:
        return sub_fml


def nnf_error(sub_fml, connective):
    sys.stderr.write('Error in negation normal forming: ' + str(connective) + '\n')
    raise SystemExit(1)



