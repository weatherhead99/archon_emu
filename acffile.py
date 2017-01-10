#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 18:19:22 2017

@author: weatherill
"""




class acffile:
    def __init__(self,fname):
        with open(fname) as f:
            self.lines = f.readlines()

    def extract_timing_script(self):
        
        def parse_timing_line(line):
            idx = int(line.split('=')[0].split('LINE')[1])
            val = line.split('=')[1].strip()
            return idx,val
        
        self.timing_lines = ( _ for _ in self.lines if _.startswith('LINE'))
        
        self.idxvals = map(parse_timing_line,self.timing_lines)
        
        
        


if __name__ == '__main__':
    fl = 'ACF_files/CCD250_e2v_Image.acf'
    
    reader = acffile(fl)
    
    reader.extract_timing_script()