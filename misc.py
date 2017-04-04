#!/usr/bin/env python

# Copyright Jacob Bennett 4/3/17

from flask import Markup

class EasterEgg:
    def askew():
        css = '<style>#links { transform: rotate(4deg); }</style>'
        return Markup(css)
