import os, glob, sys, time, signal, gc, psutil
from contextlib import contextmanager
from timeit import default_timer as timer
from subprocess import PIPE

# add the clausal folder path to the sys.path list
sys.path.insert(0, '..')

import clausifer

bench_sub = '/benchmarks/'
prover_sub = "/bddtab/"
results_sub = "/results/"
prover_exe = "bddtab"
pattern = '*.k'

TIME_LIM = 60
NOTSAT = "Psi is Not provable from Gamma"
SAT = "Psi is Provable from Gamma"
HEADING = "=".join(str("=") for a in range(25))


def bench_test(l_type, output, limit=None):
    global bench_path, results_sub, pattern, HEADING
    comp_bench = 0

    ancestor_path = get_parent_dir(os.path.abspath(__file__), 4)

    # get prover directory
    prover_dir = str(ancestor_path + os.path.join(str(prover_sub)))
    assert os.path.exists(prover_dir) == True, "The specified theorem prover cannot be found."

    # get benchmark directory
    bench_dir = str(ancestor_path + os.path.join(str(bench_sub), str(l_type)))
    assert os.path.exists(bench_dir) == True, "The specified theorem prover cannot be found."
    benchmarks = get_folders(bench_dir)
    if not limit: limit = len(benchmarks)

    # if output reqd, create result file
    if output:
        file_name = "test_" + time.strftime("%m%d-%H%M%S")
        results_dir = os.getcwd() + os.path.join(str(results_sub))
        output_file = create_file(results_dir, file_name)

    # iterate relevant benchmark folder
    for folder in benchmarks:
        no_files = 0
        sat_files = 0
        comp_bench += 1

        if comp_bench > limit: return None
        temp_path = os.path.join(bench_dir, str(folder))
        print("SUBFOLDER: " + str(folder).upper() + "\n" + HEADING)

        # start timer, print headers
        if output:
            append_out(output_file, [HEADING, str(folder).upper(), HEADING])
            start = timer()

        # iterate each file in folder, ending with .k
        for bfile in glob.glob(temp_path + '/' + pattern):
            no_files += 1
            file_name = os.path.basename(bfile)
            test_fml = str(file_import(bfile))

            # check ~a is non-sat (i.e. a is sat)
            validate_fml_a = "~(" + test_fml + ")"
            result_a = test_iff(prover_dir, validate_fml_a)
            # print("fml: " + str(result_a).strip())

            # check ~b (clausal form) is non-sat (i.e. b is sat)
            clausal_fml = str(clausifer.transform(test_fml, False))
            validate_fml_b = "~(" + clausal_fml + ")"
            result_b = test_iff(prover_dir, validate_fml_b)
            # print("clausal fml: " + str(result_b).strip())

            # either fml timed out/errored in prover
            if result_a and result_b:
                sat_result = process_result(result_a, result_b)
            else:
                sat_result = "timed out"

            if output:
                if sat_result == "timed out":
                    to_append = str(file_name) + ": "
                    if not result_a: to_append = to_append + "fml timed out "
                    if not result_b: to_append = to_append + "clausal fml timed out"

                    append_out(output_file, [to_append])
                elif not sat_result:
                    to_append = str(file_name) + ": \n fml: " + str(result_a) + "\n clausal fml: " + str(result_b)
                    append_out(output_file, [to_append])
                else:
                    sat_files += 1
                print(str(file_name) + " processed")
            else:
                print(str(file_name) + ": " + str(sat_result))
        print("\n")

        # end timer, print results, etc
        if output:
            end = timer()
            time_folder = end - start
            stat_folder = str(sat_files) + " of " + str(no_files) + " fml provable, in " + str(time_folder) + " ms."
            append_out(output_file, [str(str(folder) + " STATS:"), stat_folder])


def get_folders(folder_dir):
    ''' Returns list of folders within a given directory
        '''
    return os.listdir(folder_dir)


def get_parent_dir(filepath, ancestor):
    if ancestor == 0:
        return filepath
    else:
        return get_parent_dir(os.path.abspath(os.path.join(filepath, os.pardir)), ancestor - 1)


def create_file(filepath, filename):
    assert os.path.exists(filepath) == True, "The specified benchmark folder cannot be located."
    t_file = filepath + filename + ".txt"
    fo = open(t_file, "w+")
    fo.close
    return t_file


def process_result(inp_fml, clausal_fml):
    ''' Since both fml are negated, looks that both are not valid.
        '''
    global NOTSAT, SAT

    # both fml's are not satifiable (i.e. negated fmls provable)
    if (NOTSAT in inp_fml) and (NOTSAT in clausal_fml):
        return True
    # both fml's are satifiable (i.e. negated fmls not provable)
    elif (SAT in inp_fml) and (SAT in clausal_fml):
        return True
    else:
        return False


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


def test_iff(prover_dir, val_fml):
    global prover_exe, TIME_LIM

    # executable file path
    prover = prover_dir + "./" + prover_exe

    try:
        with time_limit(TIME_LIM):
            # initialise subprocess
            popen = psutil.Popen(prover, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
            # print(str.encode(val_fml + "\n"))
            (stdout, stderr) = popen.communicate(str.encode(val_fml + "\n"))

            if stdout:
                return stdout.decode("utf-8")
            else:
                return stderr.decode("utf-8")

    except TimeoutException as e:
        # terminate process since timed out
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


bench_test("all_subclasses", False)

