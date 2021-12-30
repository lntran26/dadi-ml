'''
Intergration test for the entire program
'''
import os
import re
import random
import string
from subprocess import getstatusoutput, getoutput
import pickle

PRG = 'dadi-ml'


def random_string():
    """generate a random filename"""

    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))


def test_usage():
    """ Prints program usage """

    for flag in ['', '-h', '--help']:
        out = getoutput(f'{PRG} {flag}')
        assert re.match("usage", out, re.IGNORECASE)


def test_usage_subcommand():
    """ Prints subcommand usage """

    for subcommand in ['generate_data', 'train', 'predict', 'plot']:
        for flag in ['', '-h', '--help']:
            out = getoutput(f'{PRG} {subcommand} {flag}')
            assert re.match("usage", out, re.IGNORECASE)


# test generate_data subcommand
def run_generate_data_sub(args, args_expected):
    """Template method for testing generate_data subcommand"""

    outfile = random_string()
    try:
        rv, out = getstatusoutput(
            f'{PRG} generate_data {" ".join(args)} --outdir {outfile}')

        # check that program executed without errors
        assert rv == 0
        # check that program does not produce any output to CLI
        assert out.strip() == ""
        # check that program produces an output file
        assert os.path.isfile(outfile)
        # check that output file has the correct format
        # this is only done briefly here as test_generate_data.py
        # is already checking output data more rigorously
        data = pickle.load(open(outfile, 'rb'))
        assert len(data) == args_expected['n_samples']

    finally:  # remove output file
        if os.path.isfile(outfile):
            os.remove(outfile)


def test_run_generate_data_sub_1():
    '''First generate_data test'''

    args = ['--model two_epoch', '--n_samples 5',
            '--sample_sizes 10', '--theta 1000']
    args_expected = {'n_samples': 5,
                     'sample_sizes': [10], 'thetas': 1000}
    run_generate_data_sub(args, args_expected)


def test_run_generate_data_sub_2():
    '''Second generate_data test'''

    args = ['--model split_mig', '--n_samples 1',
            '--sample_sizes 15 20']
    args_expected = {'n_samples': 1,
                     'sample_sizes': [15, 20], 'thetas': 1}
    run_generate_data_sub(args, args_expected)


def test_run_generate_data_bstr():
    '''Generate bootstrap data test'''

    args = ['--model two_epoch', '--n_samples 5',
            '--sample_sizes 10', '--theta 100', '--bootstrap']
    args_expected = {'n_samples': 5,
                     'sample_sizes': [10], 'thetas': 1000}
    run_generate_data_sub(args, args_expected)