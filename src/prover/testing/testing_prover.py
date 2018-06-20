import os, glob, time, signal, gc
from contextlib import contextmanager
from timeit import default_timer as timer
from subprocess import Popen, PIPE

bench_sub = '/benchmarks/'
prover_sub = "/src/"
results_sub = "/results/"
pattern = '*.k'

TIME_LIM = 60
HEADING = "=".join(str("=") for a in range(25))
VALID = "Psi is valid"
NON_VALID = "Psi is NOT valid"


def proof_test(l_type, output):
    global results_sub, pattern, HEADING, TIME_LIM

    ancestor_path = get_parent_dir(os.path.abspath(__file__), 4)
    prover_dir = get_parent_dir(os.path.abspath(__file__), 3)

    # get benchmark directory
    bench_dir = str(ancestor_path + os.path.join(str(bench_sub), str(l_type)))
    assert os.path.exists(bench_dir) == True, "The specified benchmark folder cannot be located."
    benchmarks = get_folders(bench_dir)

    # if output required, create result file
    if output:
        file_name = "results_" + time.strftime("%m%d-%H%M%S")
        results_dir = get_parent_dir(os.path.abspath(__file__), 1) + os.path.join(str(results_sub))
        print(results_dir)
        output_file = create_file(results_dir, file_name)

    # iterate relevant benchmark folder
    for folder in benchmarks:
        temp_path = os.path.join(bench_dir, str(folder))
        print("SUBFOLDER: " + str(folder).upper() + "\n" + HEADING)

        # folders separated into provable and non-provable fml
        req_outcome = folder[-1:]

        # start timer, print headers
        if output:
            append_out(output_file, [HEADING, str(folder).upper(), HEADING])

        # iterate each file in folder, ending with .k
        for bfile in glob.glob(temp_path + '/' + pattern):
            file_name = os.path.basename(bfile)
            test_fml = str(file_import(bfile))

            # send to k_prover, allow 100 seconds per fml
            start = timer()
            proof = get_proof(prover_dir, test_fml)
            end = timer()
            time_fml = end - start

            if proof: outcome = process_result(proof, req_outcome)
            else: outcome = "timed out"
                
            if output:
                to_append = str(file_name) + " was " + str(outcome) + " in " + str(time_fml)
                append_out(output_file, [to_append])
                print(str(file_name) + ": processed")
            else:
                print(str(file_name) + ": " + str(outcome))

        print("\n")


def process_result(prover_result, req_outcome):
    """ Compare our result with required result
    """
    global NON_VALID, VALID

    if not prover_result: return "Timed out"
    if req_outcome == "p":
        if prover_result.find(VALID) >= 0: return "CORRECT (valid)."
    if req_outcome == "n":
        if prover_result.find(NON_VALID) >= 0: return "CORRECT (not valid)."

    return "incorrect proof."


def get_folders(folder_dir):
    """ Returns list of folders within a given directory
    """
    return os.listdir(folder_dir)


def get_parent_dir(filepath, ancestor):
    if ancestor == 0:
        return filepath
    else:
        return get_parent_dir(os.path.abspath(os.path.join(filepath, os.pardir)), ancestor - 1)


def create_file(filepath, filename):
    assert os.path.exists(filepath) == True, "The specified folder cannot be located: " + str(filepath)
    t_file = filepath + filename + ".txt"
    fo = open(t_file, "w+")
    fo.close
    return t_file


def append_out(output_file, append_list):
    assert os.path.isfile(output_file) == True, "The output file cannot be located."
    f = open(output_file, "a")
    for w in append_list:
        f.write(w + '\r\n')
        f.close


def file_import(filename):
    # ensure problem file exists
    assert os.path.exists(filename) == True, "The specified benchmark cannot be located."

    fileobj = open(filename, "r")
    read_file = fileobj.read().rstrip("\n")
    fileobj.close()

    return read_file


# Had to call prove method as subprocess, due to issue with timing out z3 prover.
def get_proof(prover_dir, fml):
    global TIME_LIM

    # prover file path
    prover = prover_dir + "/main.py"
    expr = "\"" + fml + "\""

    try:
        with time_limit(TIME_LIM):
            # initialise subprocess
            popen = Popen(["python3.6", prover], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
            (stdout, stderr) = popen.communicate(str.encode(str(expr) + "\n"))

            if stdout:
                return stdout.decode("utf-8")
            else:
                return stderr.decode("utf-8")
    except TimeoutException:
        popen.terminate()
        gc.collect()
        return False


class TimeoutException(Exception): pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


proof_test("all_subclasses", True)
