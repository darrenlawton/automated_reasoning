from utilities import is_atomic, is_complex, my_isinstance
from parser import TOP, BOTTOM, Modality
from z3 import *


def k_prove(modal_clause):
    assert isinstance(modal_clause, dict), "k_prove wrong input type: %s" % modal_clause
    try:
        return modal_prove(modal_clause, dict(), [], dict(), dict(), dict(), 0)
    except Exception as e:
        print("Exception in proving function: ", e)
        raise SystemExit(1)


def modal_prove(modal_clause, w_set_dict, active_modalities, current_val, used_vals, z3_const_dict, w):
    """
    Given constraint set A at w, we use a SAT solver to find a satisfying valuation.

    :param modal_clause: dictionary of disjunctions at each modal context.
    :param w_set_dict: dictionary of clausal sets (A, ID, IB, D) at each w.
    :param active_modalities: classical literals nested beneath active modalities in the prior w depth.
    :param current_val: dictionary of satisfying valuations at each depth w - active OR branch.
    :param used_vals: dictionary of valuations for closed OR branches - req. to generate new modals from sat solver.
    :param z3_const_dict: dictionary of z3 appropriate BOOL constraints to add for each depth w.
    :param w: node depth relative to tableau tree.

    :return a z3 object SAT or a set of contradicting modal literals if UNSAT.
    """

    # a_z3_constraints stores constraint set A specific to w
    z3_const_dict[w], a_z3_constraints = set(), set()

    for d in (current_val, used_vals):  # initialise keys for respective dictionaries
        if w not in d.keys(): d[w] = None

    # get constraints set from modal clause for w
    if w not in w_set_dict.keys(): w_set_dict[w] = get_constraints(modal_clause, w)

    # if no constraints at w, return sat
    if not w_set_dict[w] and not active_modalities:
        return sat
    else:
        # activated modal constraint are a list of atoms - conjunction
        if active_modalities:
            z3_const_dict[w].add((And(set(get_bool(atom) for atom in active_modalities))))

        # constraint set {A} comprise conjunctions of classical disjunctions
        for modal_fml in w_set_dict[w]['A']:
            a_z3_constraints.add(Or(set(get_bool(atom) for atom in modal_fml.disjuncts)))

        z3_const_dict[w].add(And(a_z3_constraints))

        # get valuation from sat solver
        sat_check, current_val[w], used_vals[w] = get_valuation(z3_const_dict[w], current_val[w], used_vals[w])
        if sat_check == sat:
            return modal_check(modal_clause, w_set_dict, current_val, used_vals, z3_const_dict, w)
        else:
            # get modal literals responsible for (id) instances
            offending_atoms = get_modal_offenders(a_z3_constraints, active_modalities)
            return offending_atoms


def modal_check(modal_clause, w_set_dict, current_val, used_vals, z3_const_dict, w):
    """
    Checks which modal literals are activate at depth of w given the current valuation.
    If active diamonds are found, the TRANS rule is applied. All diamond branches must remain open.
    This function also applies the OR branching, by asking for new valuations given an unsat result.
    """
    box_atoms, active_diamonds = set(), set()
    w1 = w + 1

    # Get tuple comprising set of true literals and set of false literals
    valuation = process_model(current_val[w])

    # block as many modalities as possible whilst maintaining satisfiability.
    implied_modalities = get_active_modalities(w_set_dict[w]['IB'].union(w_set_dict[w]['ID']), valuation)
    for imp in implied_modalities:
        if repr(imp[0][0]) == 'box':
            box_atoms.add(imp[0][1])  # active implied boxes
        else:
            active_diamonds.add(imp[0][1])  # active implied diamonds
    # non implied diamonds
    for clause in w_set_dict[w]['D']:
        modal_atom = clause.disjuncts[0]
        active_diamonds.add((modal_atom[1]))

    # for each diamond apply trans rule; note: this results in an AND branching
    if not active_diamonds: return sat
    block_modalities = set()
    for diamond in active_diamonds:
        active_modalities = copy.copy(box_atoms)
        active_modalities.add(diamond)

        # if diamond is unsat, entire branch is unsat. Look for new valuation for w.
        diamond_check = modal_prove(modal_clause, w_set_dict, active_modalities, current_val, used_vals, z3_const_dict,
                                    w1)
        if diamond_check != sat:  # if sat, then move to next TRAN branch
            if diamond_check is None:
                # if diamond_check is none, then an (id) contained in the const set A of w1 - tableau closed
                return unsat
            else:
                if diamond_check != unsat:
                    # antecedents responsible for contradicting modal literals
                    triggers = get_modal_triggers(diamond_check, implied_modalities)
                    for atom in triggers:
                        if not my_isinstance(atom, bool): block_modalities.add(get_bool(atom))

                # ask for new valuation for w
                used_vals[w1] = None
                sat_check, current_val[w], used_vals[w] = get_valuation(z3_const_dict[w], current_val[w], used_vals[w],
                                                                        block_modalities)
                if sat_check == sat and (len(current_val[w]) > 0):
                    return modal_check(modal_clause, w_set_dict, current_val, used_vals, z3_const_dict, w)
                else:
                    return unsat
        else:
            current_val[w1], used_vals[w1] = None, None

    return sat


def get_valuation(w_constraints, current_val, used_vals, soft_constraints=None):
    """
    :param w_constraints: set constraints to add into Solver for depth w
    :param current_val: set current model for depth w.
    :param used_vals: set previously proposed model for depth w
    :param soft_constraints: set of atoms we prefer satisfied, but not necessary

    :return updated model based on constraints and previously generated valuations

    Adapted per https://stackoverflow.com/questions/11867611/z3py-checking-all-solutions-for-equation
    """
    if not used_vals: used_vals = set()

    # create instance of Solver s, and add constraints for depth w
    s = Optimize()
    s.add(w_constraints)

    if current_val:
        temp = set()
        for d in current_val:
            # d is a declaration
            if d.arity() > 0:
                raise Z3Exception("uninterpreted functions are not supported")
            # create a constant from declaration
            c = d()
            if is_array(c) or c.sort().kind() == Z3_UNINTERPRETED_SORT:
                raise Z3Exception("arrays and uninterpreted sorts are not supported")
            temp.add(c != current_val[d])
        used_vals.add(Or(temp))
        s.add(used_vals)

    if soft_constraints: (s.add_soft(And(c), 0.95) for c in soft_constraints)

    # return new sat model if found    
    if s.check() == sat:
        current_val = s.model()
    else:
        current_val = []

    return s.check(), current_val, used_vals


def get_modal_offenders(a_const_set, modal_atoms):
    """
    :param a_const_set: constraint set A for given w
    :param modal_atoms: set of active modal literals at given w

    :return set of modal literals causing contradiction
    """
    offenders = set()

    for modal_atom in modal_atoms:
        bool_atom = get_bool(modal_atom)
        a_const_set.add(And(bool_atom))
        id_check = get_valuation(a_const_set, set(), set())[0]
        if id_check == unsat: offenders.add(modal_atom)

    return offenders


def get_modal_triggers(offend_atoms, implied_modalities):
    """
    :param offend_atoms: set of offending modal atoms at given w
    :param implied_box: set of tuples representing implied boxes and implied diamonds

    :return set of antecedent atoms in modal implications
    """
    triggers = set()

    for atom in offend_atoms:
        for imp in implied_modalities:
            if atom == imp[0][1]: triggers.add(imp[1])

    return triggers


def process_model(current_val):
    """
    :param current_val: model generated by sat solver, atom is satisfied if in modal.

    :return tuple of sets comprising true and false atoms.
    """
    true_atoms, false_atoms = set(), set()

    for atom in current_val:
        if current_val[atom]:
            true_atoms.add(str(atom))
        else:
            false_atoms.add(str(atom))

    return true_atoms, false_atoms


def get_active_modalities(modal_implications, valuation):
    """
    :param modal_implications: set of modal implications represented as clauses
    :param valuation: tuple of true set and false set

    :return set of tuples representing active modal implications (modal atom, classical atom)

    """
    active_modal = set()

    for modal_clause in modal_implications:
        # check if modal literal activated
        active = check_activation(modal_clause, valuation)
        if active: active_modal.add(active)

    # check potential to deactivate modalities
    # don't need maximality - that is, if atom is not in true_lits then can assume false.
    return deactivate_modalities(active_modal, valuation)


def check_activation(modal_implication, valuation):
    """
    :param modal_implication: see active_modalities above
    :param valuation: see active_modalities above

    :return tuple representing modal implications (modal atom, classical atom) if modality is active.
    otherwise, return False.
    """
    assert len(
        modal_implication.disjuncts) <= 2, "The modal disjunction is not formed correctly: %s" % modal_implication
    prop_atom, modal_atom = None, None
    true_literals = valuation[0]
    false_literals = valuation[1]

    # given assertion there should be one prop atom and one modal atom
    for disjunct in modal_implication.disjuncts:
        if not is_complex(disjunct):
            prop_atom = disjunct
        elif my_isinstance(disjunct[0], Modality):
            modal_atom = disjunct

    # check valuation of prop_atom, to determine num_modal_atoms activity
    # check if prop_atom is negated
    if is_atomic(prop_atom) and str(prop_atom) not in true_literals:
        # not negated
        return modal_atom, prop_atom

    if not is_atomic(prop_atom) and str(prop_atom[1]) not in false_literals:
        return modal_atom, prop_atom

    return False


def deactivate_modalities(active_modal_set, valuation):
    """
    :param active_modal_set: set of active modal implications (modal atom, classical atom)

    :return list of modal implications that remain active, after trying to deactivate by satisfying antecedent.
    """
    active_modal = set()

    s = Optimize()
    # add current valuation to solver
    s.add((And(set(Bool(lit) for lit in valuation[0]))))
    s.add((And(set(Not(Bool(lit)) for lit in valuation[1]))))

    for imp_modalities in active_modal_set:
        s.add_soft(And(get_bool(imp_modalities[1])), 1)

    s.check()
    valuation = process_model(s.model())

    for imp_modalities in active_modal_set:
        prop_ante = imp_modalities[1]
        if is_atomic(prop_ante) and (prop_ante not in valuation[0]):
            active_modal.add(imp_modalities)
        if not is_atomic(prop_ante) and prop_ante[1] not in valuation[1]:
            active_modal.add(imp_modalities)

    return active_modal


def get_bool(atom):
    """
    :param atom: parsed classical atom, can be negated

    :return z3 appropriate boolean value
    """
    assert not is_complex(atom), "Error adding atom to sat solver: %s" % atom

    # need to account for 'False' and 'True'
    if is_atomic(atom):
        if atom == TOP:
            return True
        elif atom == BOTTOM:
            return False
        else:
            return Bool(str(atom))
    elif str(atom[0]) == '~':
        if atom[1] == TOP:
            return False
        elif atom[1] == BOTTOM:
            return True
        else:
            return Not(Bool(str(atom[1])))
    else:  # error
        sys.stderr.write('Error adding atom to sat solver: ' + str(atom) + '\n')
        raise SystemExit(1)


def get_constraints(modal_clause_dict, w):
    """
    :return parses modal clauses for input w and returns dictionary of following clauses:
        A disjunction of classical literals
        IB disjunction of one box literal and one classical literal
        ID disjunction of one diamond literal and one classical literal
        D single diamond literal
    """
    A = set()
    IB = set()
    ID = set()
    D = set()

    if w in modal_clause_dict.keys():
        w_modal_clauses = modal_clause_dict[w]
        # modal_clause is a ModalExpr - modal context and list of disjunctions
        for modal_clause in w_modal_clauses:
            disjunction = modal_clause.disjuncts

            if len(disjunction) > 2:
                A.add(modal_clause)
            elif len(disjunction) == 1:
                if not is_complex(disjunction[0]):
                    A.add(modal_clause)
                else:
                    assert get_modality(disjunction) == 'dia', \
                        "Error in getting constraint sets - incorrectly formed modal clause: %s" % modal_clause
                    D.add(modal_clause)  # if complex, has to be single dia literal
            else:  # by deduction, only two disjuncts in modal_clause
                mod = get_modality(disjunction)
                if mod == 'box':
                    IB.add(modal_clause)
                elif mod == 'dia':
                    ID.add(modal_clause)
                else:
                    A.add(modal_clause)

    return {'A': A, 'IB': IB, 'ID': ID, 'D': D}


def get_modality(disjunctions):
    """
    :param disjunctions: list of disjunctions

    :return first stripped modal literal
    """
    for disjunct in disjunctions:
        if is_complex(disjunct):
            connective = disjunct[0]
            if my_isinstance(connective, Modality): return repr(connective)
    return False
