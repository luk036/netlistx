# -*- coding: utf-8 -*-
from __future__ import print_function

import numpy as np

from netlistx.cutting_plane import cutting_plane_optim
from netlistx.ell import Ell
from netlistx.ell_typing import OracleFeas, OracleOptim


class MyOracleFeas(OracleFeas):
    idx = 0

    # constraint 1: x + y <= 3
    def fn1(self, x, y):
        return x + y - 3

    # constraint 2: x - y >= 1
    def fn2(self, x, y):
        return -x + y + 1

    def grad1(self):
        return np.array([1.0, 1.0])

    def grad2(self):
        return np.array([-1.0, 1.0])

    def __init__(self):
        self.fns = (self.fn1, self.fn2)
        self.grads = (self.grad1, self.grad2)

    def assess_feas(self, z):
        """[summary]

        Arguments:
            z ([type]): [description]

        Returns:
            [type]: [description]
        """
        x, y = z

        for _ in [0, 1]:
            self.idx += 1
            if self.idx == 2:
                self.idx = 0  # round robin
            if (fj := self.fns[self.idx](x, y)) > 0:
                return self.grads[self.idx](), fj
        return None


class MyOracle(OracleOptim):
    helper = MyOracleFeas()

    def assess_optim(self, z, gamma: float):
        """[summary]

        Arguments:
            z ([type]): [description]
            gamma (float): the best-so-far optimal value

        Returns:
            [type]: [description]
        """
        if cut := self.helper.assess_feas(z):
            return cut, None
        x, y = z
        # objective: maximize x + y
        f0 = x + y
        if (fj := gamma - f0) > 0.0:
            return (-1.0 * np.array([1.0, 1.0]), fj), None

        gamma = f0
        return (-1.0 * np.array([1.0, 1.0]), 0.0), gamma


class MyOracleFeas2(OracleFeas):
    idx = 0

    # constraint 1: x + y <= 3
    def fn1(self, x, y):
        return x + y - 3

    # constraint 2: x - y >= 1
    def fn2(self, x, y):
        return -x + y + 1

    def grad1(self):
        return np.array([1.0, 1.0])

    def grad2(self):
        return np.array([-1.0, 1.0])

    def __init__(self):
        self.fns = (self.fn1, self.fn2)
        self.grads = (self.grad1, self.grad2)

    def assess_feas(self, z):
        """[summary]

        Arguments:
            z ([type]): [description]

        Returns:
            [type]: [description]
        """
        x, y = z

        for _ in [0, 1]:
            self.idx += 1
            if self.idx == 2:
                self.idx = 0  # round robin
            if (fj := self.fns[self.idx](x, y)) > 0:
                return self.grads[self.idx](), fj
        return None


class MyOracle2(OracleOptim):
    helper = MyOracleFeas2()

    def assess_optim(self, z, gamma: float):
        """[summary]

        Arguments:
            z ([type]): [description]
            gamma (float): the best-so-far optimal value

        Returns:
            [type]: [description]
        """
        if cut := self.helper.assess_feas(z):
            return cut, None
        x, y = z
        # objective: maximize x + y
        f0 = x + y
        if (fj := gamma - f0) > 0.0:
            return (-1.0 * np.array([1.0, 1.0]), fj), None

        gamma = f0
        return (-1.0 * np.array([1.0, 1.0]), 0.0), gamma


def run_example1(omega):
    xinit = np.array([0.0, 0.0])  # initial xinit
    ellip = Ell(10.0, xinit)
    xbest, _, num_iters = cutting_plane_optim(omega(), ellip, float("-inf"))
    assert xbest is not None
    return num_iters


def test_with_round_robin(benchmark):
    num_iters = benchmark(run_example1, MyOracle)
    assert num_iters == 20


def test_without_round_robin(benchmark):
    num_iters = benchmark(run_example1, MyOracle2)
    assert num_iters == 20
