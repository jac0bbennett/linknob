#!/usr/bin/env python

# Copyright Jacob Bennett 8/3/16

from sqlalchemy import func

def score(points, age, users):
    score = ((points / age) / users)
    return score
