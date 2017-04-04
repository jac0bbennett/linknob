#!/usr/bin/env python

# Copyright Jacob Bennett 4/4/17

from flask import Markup

class EasterEgg:
    def __init__(self):
        self.eggs = {'askew': self.askew(), 'upside down': self.upsideDown(), 'fake news': self.fakenews()}

    def askew(self):
        css = '<style>#links { transform: rotate(4deg); }</style>'
        return Markup(css)

    def upsideDown(self):
        css = '<style>#links { transform: rotate(180deg); }</style>'
        return Markup(css)

    def fakenews(self):
        html = '<span id="fakenews" style="float:right;">CNN</span><script>$("#fakenews").fadeOut(1200);</script>'
        return Markup(html)

    def getEggs(self):
        return self.eggs

    def runEgg(self, egg):
        if egg in self.eggs:
            return self.eggs[egg]
        else:
            return None
