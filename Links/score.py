#!/usr/bin/env python

# Copyright Jacob Bennett 8/3/16

from sqlalchemy import func

def score(points, linktime, users):
    age = func.extract('epoch', func.current_timestamp() - linktime)
    score = ((points / age) / users)
    return score
