#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: stat.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>
import numpy as np


class StatCounter(object):
    def __init__(self):
        self.values = []

    def feed(self, v):
        self.values.append(v)

    @property
    def average(self):
        return np.mean(self.values)

    @property
    def sum(self):
        return np.sum(self.values)

class Accuracy(object):
    def __init__(self):
        self.tot = 0
        self.corr = 0

    def feed(self, corr, tot=1):
        self.tot += tot
        self.corr += corr

    @property
    def accuracy(self):
        if self.tot < 0.001:
            return 0
        return self.corr * 1.0 / self.tot

