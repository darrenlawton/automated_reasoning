import parser


def my_isinstance(in_object, in_class):
    """
    :param in_object: an object
    :param in_class: a class

    :return: returns boolean value if class names match
    """
    return in_object.__class__.__name__ == in_class.__name__


def op(operator):
    """
    :param operator: a string representing a logical connective

    :return: an operator object
    """
    return parser.Operator(operator)


def is_atomic(fml):
    """
    :param fml: a string representing a logical expression

    :return: true if input expression is an atom.
    """
    return my_isinstance(fml, parser.Atomic)


def is_complex(fml):
    """
    :param fml: a string representing a logical expression

    :return: true if fml is a complex.
    """
    if is_atomic(fml):
        return False
    else:
        return not (repr(fml[0]) == '~' and is_atomic(fml[1]))
