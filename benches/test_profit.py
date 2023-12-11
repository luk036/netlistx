# -*- coding: utf-8 -*-
from __future__ import print_function

import numpy as np

from netlistx.cutting_plane import cutting_plane_optim, cutting_plane_optim_q
from netlistx.ell import Ell
from netlistx.ell_stable import EllStable
from netlistx.oracles.profit_oracle import ProfitOracle, ProfitQOracle, ProfitRbOracle

p, A, k = 20.0, 40.0, 30.5
params = p, A, k
alpha, beta = 0.1, 0.4
v1, v2 = 10.0, 35.0
a = np.array([alpha, beta])
v = np.array([v1, v2])
r = np.array([100.0, 100.0])  # initial ellipsoid (sphere)


def run_profit(E):
    ellip = E(r, np.array([0.0, 0.0]))
    omega = ProfitOracle(params, a, v)
    xbest, _, num_iters = cutting_plane_optim(omega, ellip, 0.0)
    assert xbest is not None
    return num_iters


def run_profit_rb(E):
    e1 = 0.003
    e2 = 0.007
    e3 = e4 = e5 = 1.0
    ellip = E(r, np.array([0.0, 0.0]))
    omega = ProfitRbOracle(params, a, v, (e1, e2, e3, e4, e5))
    xbest, _, num_iters = cutting_plane_optim(omega, ellip, 0.0)
    assert xbest is not None
    return num_iters


def run_profit_q(E):
    ellip = E(r, np.array([0.0, 0.0]))
    omega = ProfitQOracle(params, a, v)
    xbest, _, num_iters = cutting_plane_optim_q(omega, ellip, 0.0)
    assert xbest is not None
    return num_iters


def test_profit_ell(benchmark):
    num_iters = benchmark(run_profit, Ell)
    assert num_iters == 36


def test_profit_ell_stable(benchmark):
    num_iters = benchmark(run_profit, EllStable)
    assert num_iters == 36


def test_profit_rb_ell(benchmark):
    num_iters = benchmark(run_profit_rb, Ell)
    assert num_iters == 41


def test_profit_rb_ell_stable(benchmark):
    num_iters = benchmark(run_profit_rb, EllStable)
    assert num_iters == 41


def test_profit_q_ell(benchmark):
    num_iters = benchmark(run_profit_q, Ell)
    assert num_iters == 29


def test_profit_q_ell_stable(benchmark):
    num_iters = benchmark(run_profit_q, EllStable)
    assert num_iters == 29
