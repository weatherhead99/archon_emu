#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 18:19:22 2017

@author: weatherill
"""


from configparser import ConfigParser

class acffile:
    def __init__(self,fname):
        self.cp = ConfigParser()
        self.cp.read(fname)
            
    @property
    def timing_script(self):        
        if not hasattr(self,'_timingscript'):
            nlines = self.cp['CONFIG'].getint('LINES')
            self._timingscript = [ self.cp['CONFIG']['LINE%d' %_] for _ in range(nlines)]
        
        return self._timingscript

        
    
            
        
        
        


if __name__ == '__main__':
    import os
    os.chdir('../seqs')
    fl = 'CCD250_20161109_LOW_GAIN-reversed-xed.acf'
    #fl = '../seqs/CCD250_20161109_LOW_GAIN-reversed-xed.acf'
    
    archon_conf = acffile(fl)
    