# -*- coding: utf-8 -*-
from __future__ import print_function

import numpy as np

from netlistx.cutting_plane import cutting_plane_feas
from netlistx.ell import Ell
from netlistx.ell_typing import OracleFeas


class MyOracle(OracleFeas):
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


class MyOracle2(OracleFeas):
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

        for self.idx in [0, 1]:
            if (fj := self.fns[self.idx](x, y)) > 0:
                return self.grads[self.idx](), fj
        return None


def run_example2(omega):
    xinit = np.array([2.0, 2.0])  # initial xinit
    ellip = Ell(10.0, xinit)
    xbest, num_iters = cutting_plane_feas(omega(), ellip)
    assert xbest is not None
    return num_iters


def test_with_round_robin(benchmark):
    num_iters = benchmark(run_example2, MyOracle)
    assert num_iters == 2


def test_without_round_robin(benchmark):
    num_iters = benchmark(run_example2, MyOracle2)
    assert num_iters == 2
