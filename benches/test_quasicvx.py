# -*- coding: utf-8 -*-
from __future__ import print_function

import math

import numpy as np

from netlistx.cutting_plane import cutting_plane_optim
from netlistx.ell import Ell
from netlistx.ell_typing import OracleOptim


class MyQuasicvxOracle(OracleOptim):
    idx: int = 0  # for round robin
    tmp2: float
    tmp3: float

    def __init__(self):
        self.fns = (self.fn1, self.fn2)
        self.grads = (self.grad1, self.grad2)

    # constraint 1: exp(x) <= y, or sqrtx**2 <= ly
    def fn1(self, sqrtx, ly, _):
        return sqrtx * sqrtx - ly

    # objective: minimize -sqrt(x) / y
    def fn2(self, sqrtx, ly, gamma):
        self.tmp2 = math.exp(ly)
        self.tmp3 = gamma * self.tmp2
        return -sqrtx + self.tmp3

    def grad1(self, sqrtx):
        return np.array([2 * sqrtx, -1.0])

    def grad2(self, _):
        return np.array([-1.0, self.tmp3])

    def assess_optim(self, z, gamma: float):
        """[summary]

        Arguments:
            z ([type]): [description]
            gamma (float): the best-so-far optimal value

        Returns:
            [type]: [description]
        """
        sqrtx, ly = z

        for _ in [0, 1]:
            self.idx += 1
            if self.idx == 2:
                self.idx = 0  # round robin
            if (fj := self.fns[self.idx](sqrtx, ly, gamma)) > 0:
                return (self.grads[self.idx](sqrtx), fj), None

        gamma = sqrtx / self.tmp2
        return (np.array([-1.0, sqrtx]), 0), gamma


class MyQuasicvxOracle2(OracleOptim):
    idx: int = 0  # for round robin
    tmp2: float
    tmp3: float

    def __init__(self):
        self.fns = (self.fn1, self.fn2)
        self.grads = (self.grad1, self.grad2)

    # constraint 1: exp(x) <= y, or sqrtx**2 <= ly
    def fn1(self, sqrtx, ly, _):
        return sqrtx * sqrtx - ly

    # objective: minimize -sqrt(x) / y
    def fn2(self, sqrtx, ly, gamma):
        self.tmp2 = math.exp(ly)
        self.tmp3 = gamma * self.tmp2
        return -sqrtx + self.tmp3

    def grad1(self, sqrtx):
        return np.array([2 * sqrtx, -1.0])

    def grad2(self, _):
        return np.array([-1.0, self.tmp3])

    def assess_optim(self, z, gamma: float):
        """[summary]

        Arguments:
            z ([type]): [description]
            gamma (float): the best-so-far optimal value

        Returns:
            [type]: [description]
        """
        sqrtx, ly = z

        for self.idx in [0, 1]:
            if (fj := self.fns[self.idx](sqrtx, ly, gamma)) > 0:
                return (self.grads[self.idx](sqrtx), fj), None

        gamma = sqrtx / self.tmp2
        return (np.array([-1.0, sqrtx]), 0), gamma


def run_quasicvx(omega):
    xinit = np.array([0.0, 0.0])  # initial xinit
    ellip = Ell(10.0, xinit)
    xbest, _, num_iters = cutting_plane_optim(omega(), ellip, 0.0)
    assert xbest is not None
    return num_iters


def test_with_round_robin(benchmark):
    num_iters = benchmark(run_quasicvx, MyQuasicvxOracle)
    assert num_iters == 35


def test_without_round_robin(benchmark):
    num_iters = benchmark(run_quasicvx, MyQuasicvxOracle2)
    assert num_iters == 43
