import time

import numpy as np

from netlistx.cutting_plane import Options, cutting_plane_optim
from netlistx.ell import Ell
from netlistx.oracles.lowpass_oracle import create_lowpass_case


def run_lowpass(use_parallel_cut: bool, duration=0.000001):
    """[summary]

    Arguments:
        use_parallel_cut (float): [description]

    Keyword Arguments:
        duration (float): [description] (default: {0.000001})

    Returns:
        [type]: [description]
    """
    N = 32
    r0 = np.zeros(N)  # initial xinit
    r0[0] = 0
    ellip = Ell(4.0, r0)
    ellip._helper.use_parallel_cut = use_parallel_cut
    omega, Spsq = create_lowpass_case(N)
    options = Options()
    options.max_iters = 20000
    options.tol = 1e-8
    h, _, num_iters = cutting_plane_optim(omega, ellip, Spsq, options)
    time.sleep(duration)
    return num_iters, h is not None


def test_lowpass(benchmark):
    """Test the lowpass case with parallel cut"""
    result, feasible = benchmark(run_lowpass, True)
    assert feasible
    assert result >= 1075
    assert result <= 1194


def test_no_parallel_cut(benchmark):
    """Test the lowpass case with no parallel cut"""
    result, feasible = benchmark(run_lowpass, False)
    assert feasible
    assert result >= 13268
