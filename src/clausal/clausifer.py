import clausify
import nnf
import parser
import simplify


def transform(formula, output):
    """
    :param formula: String representation of a modal formula.
    The syntax for such a formula is per the grammar as stipulated in the README.
    Example input: "(a|b) & (~c => d)"
    :param output: boolean value.

    :return: if output is true, prints modal clausal form (mcf) of transformed formula.
    Otherwise returns mcf as dictionary.
    """
    try:
        modal_clause = clausify.clausify(simplify.simplify(nnf.to_nnf(parser.parse(formula))))  # type: dictionary

        if output:
            print(clausify.to_string(modal_clause))
        else:
            return modal_clause
            
    except RuntimeError as re:
        print('Unable to form modal clause: {}'.format(re.args[0]))
        raise SystemExit(1)