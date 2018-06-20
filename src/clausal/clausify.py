"""
Module to transform formula into in modal clausal form.
Where the formula is in negation normal form.
"""
import copy
import sys

import parser
import utilities as u

max_mc_id = 0
p_id = 0


def clausify(nnf_formula):
    """
    :param nnf_formula: formula in negation normal form represented as an AST.
    :return: dictionary representing the modal clausal form (mcf) of the formula.
    """
    global p_id

    try:
        p_id = 0
        id_mc = 0
        ext_mc = get_mc(nnf_formula, [])
        return to_mcf(ext_mc[0], ext_mc[1], dict(), id_mc)
    except Exception as e:
        print ('Exception in transforming to clausal form: {}'.format(e.args[0]))
        raise SystemExit(1)


def mcf_classical_atom(modal_context, fml, clausal_form_dict, id_mc):
    """ Takes classical literal (fml), and adds to relevant disjunction.
    """
    assert not u.is_complex(fml)
    create_mc(modal_context, id_mc, clausal_form_dict, fml)


def mcf_or(modal_context, fml, clausal_form_dict, id_mc):
    """ Takes OR fml, and applies transformation rules.
    """
    global max_mc_id
    mcf_dict_key = len(modal_context)
    modal_context_clauses = False

    # modal context does not distribute over the 'or' operator
    left_fml = fml[1]
    right_fml = fml[2]

    # if both formulas are simple, add to context
    if not u.is_complex(left_fml) or not u.is_complex(right_fml):
        if not u.is_complex(left_fml) and not u.is_complex(right_fml):
            to_mcf(modal_context, left_fml, clausal_form_dict, id_mc)
            to_mcf(modal_context, right_fml, clausal_form_dict, id_mc)
        else:  # one of the formulas must be complex - &, | or modality
            if u.is_complex(right_fml):
                complex_fml = right_fml
                simple_fml = left_fml
            else:
                complex_fml = left_fml
                simple_fml = right_fml

            # check simple_fml is only other conjunct in context
            if mcf_dict_key in clausal_form_dict:
                modal_context_clauses = eq_modal_context(modal_context, id_mc, clausal_form_dict[mcf_dict_key])
            complex_fml_connective = complex_fml[0]

            if repr(complex_fml_connective) == '|' or modal_context_clauses:
                to_mcf(modal_context, simple_fml, clausal_form_dict, id_mc)
                to_mcf(modal_context, complex_fml, clausal_form_dict, id_mc)
            elif repr(complex_fml_connective) == '&':
                # simple_fml is only other conjunct in context therefore apply de morgans
                com_left_fml = complex_fml[1]
                com_right_fml = complex_fml[2]
                to_mcf(modal_context, [u.op('&'), [u.op('|'), simple_fml, com_left_fml], [u.op('|'), simple_fml, com_right_fml]],
                       clausal_form_dict, id_mc)
            elif isinstance(complex_fml_connective, parser.Modality):
                # simple_fml is only other conjunct in context
                to_mcf(modal_context, simple_fml, clausal_form_dict, id_mc)
                to_mcf(modal_context, complex_fml, clausal_form_dict, id_mc, False)

            else:
                mcf_error(modal_context, fml, clausal_form_dict, id_mc)

    else:  # both arguments are complex sub formulas
        to_mcf(modal_context, left_fml, clausal_form_dict, id_mc, True)
        to_mcf(modal_context, right_fml, clausal_form_dict, id_mc, True)


def mcf_and(modal_context, fml, clausal_form_dict, id_mc, distributive):
    """ Takes AND fml, and applies transformation rules.
    """
    global max_mc_id

    left_fml = fml[1]
    right_fml = fml[2]
    max_mc_id = max(id_mc, max_mc_id)

    # if modal context distributes over the 'and' operator
    if not distributive:
        left_mc = get_mc(left_fml, copy.deepcopy(modal_context))
        max_mc_id += 1
        to_mcf(left_mc[0], left_mc[1], clausal_form_dict, max_mc_id)

        right_mc = get_mc(right_fml, copy.deepcopy(modal_context))
        max_mc_id += 3
        to_mcf(right_mc[0], right_mc[1], clausal_form_dict, max_mc_id)

    else:
        p_atom = create_atom()
        to_mcf(modal_context, p_atom, clausal_form_dict, id_mc)
        updated_fml = [u.op('|'), [u.op('~'), p_atom], fml]
        max_mc_id += 1
        to_mcf(modal_context, updated_fml, clausal_form_dict, max_mc_id, distributive=False)


def mcf_modality(modal_context, fml, clausal_form_dict, id_mc, distributive):
    """ Takes MODAL fml, and applies transformation rules.
    """
    global max_mc_id

    # print("MODAL " + str(fml) + ", id: " + str(id_mc))

    nested_fml = fml[1]
    max_mc_id = max(id_mc, max_mc_id)

    if not distributive:
        if not u.is_complex(nested_fml):
            create_mc(modal_context, id_mc, clausal_form_dict, fml)
        else:  # nested_fml is complex
            disjunctive_atoms = get_num_atoms(modal_context, id_mc, clausal_form_dict)
            p_atom = create_atom()

            # no classical literal in disjunction, therefore add false
            if disjunctive_atoms == 0:
                false_literal = parser.Atomic(parser.BOTTOM)
                create_mc(modal_context, id_mc, clausal_form_dict, false_literal)

            # complex modal formula with one classical literal in disjunction
            if disjunctive_atoms <= 1:
                max_mc_id += 2
                create_mc(modal_context, id_mc, clausal_form_dict, [fml[0], p_atom])

                updated_modal_context = copy.deepcopy(modal_context)
                updated_modal_context.append(parser.Modality('box', fml[0].id))
                upd_fml = [u.op('|'), [u.op('~'), p_atom], nested_fml]

                to_mcf(updated_modal_context, upd_fml, clausal_form_dict, max_mc_id, distributive=False)

            else:
                to_mcf(modal_context, fml, clausal_form_dict, id_mc, True)

    else:  # complex modal fml nested within OR connective
        p_atom = create_atom()
        to_mcf(modal_context, p_atom, clausal_form_dict, id_mc)
        upd_fml = [u.op('|'), [u.op('~'), p_atom], fml]
        max_mc_id += 2
        to_mcf(modal_context, upd_fml, clausal_form_dict, max_mc_id, distributive=False)


def mcf_error(modal_context, fml, clausal_form_dict, id_mc):
    sys.stderr.write('Error in clausal forming: ' + str(fml) + '\n')
    raise SystemExit(1)


def to_mcf(modal_context, nnf_fml, clausal_form_dict, id_mc, distributive=False):
    """ Given an expression in nnf (nnf_fml), return an equivalent expression in modal clausal form.
    """
    if nnf_fml and u.is_complex(nnf_fml):
        connective = repr(nnf_fml[0])
        switch = {
            '&': mcf_and,
            '|': mcf_or,
            'box': mcf_modality,
            'dia': mcf_modality,
        }
        operation = switch.get(connective, mcf_error)
        if operation == mcf_and or operation == mcf_modality:
            operation(modal_context, nnf_fml, clausal_form_dict, id_mc, distributive)
        else:
            operation(modal_context, nnf_fml, clausal_form_dict, id_mc)

    else:
        # expr is a classical literal, add to relevant disjunct
        mcf_classical_atom(modal_context, nnf_fml, clausal_form_dict, id_mc)

    return clausal_form_dict


def create_atom():
    """ Return new literal with unique p_id
    """
    global p_id
    p_id += 1
    return parser.Atomic('p_' + str(p_id - 1))


def get_mc(fml, modal_context):
    """ Returns a tuple, specifically the modal context (MC) and remaining expression.
    Note, MC is a possibly empty sequence of universal box-like modal operators.
    """
    if not u.is_atomic(fml):
        connective = repr(fml[0])
        if connective == 'box':
            modal_context.append(fml[0])
            return get_mc(fml[1], modal_context)
        else:
            return [modal_context, fml]
    else:
        return [modal_context, fml]


def create_mc(modal_context, id_modal_context, clausal_form_dict, *args):
    """ The clausal form (clausal_form_dict) is stored as dictionary where len(modal_context) is the key, and a list of ModalExpr objects are the value.
    This method adds literals (args) to the relevant ModalExpr - a disjuction.
    """
    global max_mc_id
    max_mc_id = max(id_modal_context, max_mc_id)
    mcf_dict_key = len(modal_context)

    for arg in args:
        if not mcf_dict_key in clausal_form_dict:
            # create dict key, and add disjunct to relevant list (based on id)
            clausal_form_dict[mcf_dict_key] = [
                ModalExpr(modal_context, id_modal_context, arg)]
            continue

        modal_context_clauses = eq_modal_context(modal_context, id_modal_context, clausal_form_dict[mcf_dict_key])
        if modal_context_clauses:
            add_disjunct = modal_context_clauses.add_disjunct(arg)
            # if add_disjunct returns non empty, need to create clause for modal literal
            if add_disjunct:
                max_mc_id += 2
                to_mcf(modal_context, add_disjunct, clausal_form_dict, max_mc_id)
        else:
            clausal_form_dict[mcf_dict_key].append(ModalExpr(copy.deepcopy(modal_context), id_modal_context, arg))


def eq_modal_context(modal_context, id_modal_context, clausal_seq):
    """ If there is an equivalent modal context in seq; return it.
    """
    for mc in clausal_seq:
        if mc.__eq__(modal_context, id_modal_context):
            return mc
    return False


def get_num_atoms(modal_context, id_modal_context, clausal_form_dict):
    """ Returns number of classical literals in given modal context (returns max 2).
    """
    classic_atoms = 0
    mcf_dict_key = len(modal_context)

    if not mcf_dict_key in clausal_form_dict: return 0  # disjunction has not been created

    modal_context_clauses = eq_modal_context(modal_context, id_modal_context, clausal_form_dict[mcf_dict_key])
    if modal_context_clauses:
        for disjunct in modal_context_clauses.disjuncts:
            if not u.is_complex(disjunct):
                classic_atoms += 1
                if classic_atoms > 1: return 2
            elif isinstance(disjunct[0], parser.Modality):
                return 2
        return 1
    else:
        return 0  # disjunction (mc and id) has not been created


def to_string(clausal_form_dict):
    output = ""

    for key in clausal_form_dict.keys():
        for disjunction in clausal_form_dict[key]:
            if output == "":
                output = str(disjunction)
            else:
                output = output + " & " + str(disjunction)
    return output


def get_str(fml):
    """ Returns string for unary operators in correct syntactic form
    """
    if u.is_atomic(fml):
        return str(fml)
    else:
        unary_connective = fml[0]
        if repr(unary_connective) == '~':
            return '~' + get_str(fml[1])
        elif repr(unary_connective) == 'box':
            return '[' + unary_connective.id + ']' + get_str(fml[1])
        elif repr(unary_connective) == 'dia':
            return '<' + unary_connective.id + '>' + get_str(fml[1])


def get_tuple(atom):
    """ if atom is negated or modal returns tuple representation
    """
    if u.is_atomic(atom):
        return atom
    else:
        return atom[0], get_tuple(atom[1])


class ModalExpr:
    def __init__(self, modal_context, id_modal_context, *args):
        """
        Modal_cont is a possible empty list of box like operators;
        disjuncts is a list of literals.
        """
        self.mc = modal_context
        self.mcid = id_modal_context
        self.disjuncts = []
        self.num_prop_atoms = 0
        self.num_modal_atoms = 0

        if args:
            for arg in args: self.add_disjunct(arg)

    def __repr__(self):
        disjuncts = []

        for disjunct in self.disjuncts:
            disjuncts.append(disjunct)

        return str([self.mc, disjuncts])

    def __str__(self):
        modal_ctx = ""
        disjuncts = ""

        for disj in self.disjuncts:
            if disjuncts == "":
                disjuncts = get_str(disj)
            else:
                disjuncts = disjuncts + " | " + get_str(disj)

        if len(self.mc) > 0:
            for ctx in self.mc:
                modal_ctx = modal_ctx + str(ctx)
            return "(" + modal_ctx + " (" + disjuncts + "))"
        else:
            return "(" + disjuncts + ")"

    def __eq__(self, mc, id_modal_context):
        if self.mcid != id_modal_context:
            return False
        elif self.mc == mc:
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.mcid)

    def add_disjunct(self, arg):
        """ Add modal and classical literals to disjunction. Checks to ensure modal clauses are well formed.
        """
        if not u.is_complex(arg):  # not complex, as in classical literal
            self.disjuncts.append(get_tuple(arg))
            self.num_prop_atoms += 1

            if self.num_modal_atoms >= 1 and self.num_prop_atoms > 1:
                offending_atom = self.get_modal_lit()
                return self.adjust_modal_literal(offending_atom)
            else:
                return None
        elif isinstance(arg[0], parser.Modality):
            if self.num_modal_atoms == 0 and self.num_prop_atoms <= 1:
                self.disjuncts.append(get_tuple(arg))
                self.num_modal_atoms += 1
                return None
            else:
                return self.adjust_modal_literal(arg)

        else:
            mcf_error(self.mc, arg, self.disjuncts, self.mcid)

    def get_modal_lit(self):
        """ Returns first modal atom in a given disjunction.
        """
        for disjunct in self.disjuncts:
            if u.is_complex(disjunct):
                if isinstance(disjunct[0], parser.Modality):
                    self.disjuncts.remove(disjunct)
                    return disjunct
        return None

    def adjust_modal_literal(self, offending_atom):
        """ Moves offending modal literal into new disjunction
        """
        p_atom = create_atom()
        self.disjuncts.append(p_atom)
        return [u.op('|'), [u.op('~'), p_atom], offending_atom]
