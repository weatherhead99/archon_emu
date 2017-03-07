#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 17:58:17 2017

@author: weatherill
"""

import argparse
from archon_emu import acffile

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="dumps timing script information from archon configuration file"
                                 )
    
    ap.add_argument("infile",type=str, help="input file (archon configuration file)")
    ap.add_argument("-o", dest="outfile", type=str,help="output file for timing script. Prints to stdout if not provided")
    
    
    args = ap.parse_args()
    
    use_stdout = False if args.outfile else True
    
    
    with open(args.infile,"r") as f:
        st = f.read()
    
    fl = acffile.ArchonConfig(st)
    
    
    if(use_stdout):
        print(fl.timing_script + "\n")
        
    else:
        with open(args.outfile,"w") as f:
            f.write(fl.timing_script + "\n")
            
    
    
    