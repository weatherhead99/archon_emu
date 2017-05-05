#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  5 14:16:46 2017

@author: weatherill
"""

import argparse
from archon_emu import acffile

def strip_state_key(line):
    return line[line.index('\\')+1:]

def get_states_lines(acffile,strip= False):
    n_states = acffile.cp['CONFIG'].getint('STATES')    
    modpos = [_.position for _ in acffile.modules]
    
    for i in range(n_states):
        namekey = 'STATE%d\\NAME' % i
        controlkey = 'STATE%d\\CONTROL' %i
        
        name = acffile.cp['CONFIG'][namekey]
        control = acffile.cp['CONFIG'][controlkey]
        
        if strip:
            thisstatelines = [strip_state_key(namekey + '=' + name), strip_state_key(controlkey + '=' + control)]
        else:
            thisstatelines = [namekey + '=' + name, controlkey + '=' + control]
        
        for j in modpos:
            k = 'STATE%d\\MOD%d' % (i,j)
            try:
                v = acffile.cp['CONFIG'][k]                
                if strip:
                    thisstatelines.append(strip_state_key(k + '=' + v))
                else:
                    thisstatelines.append(k + '=' + v)
            except KeyError:
                continue        
        yield thisstatelines




if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="dumps timing states from ACF file")
    
    ap.add_argument("infile", type=str, help="input archon configuration file")
    ap.add_argument("-o", dest="outfile", type=str, help="output file for timing states. Prints to stdout if not present")
    ap.add_argument('-s,--strip',dest="strip",action='store_true',help="strip module part from keys")
    
    args = ap.parse_args()
    
    use_stdout = False if args.outfile else True
    
    with open(args.infile,"r") as f:
        st = f.read()
        
    fl = acffile.ArchonConfig(st)
    
    
    statelines = get_states_lines(fl,args.strip)

    if args.outfile:
        with open(args.outfile,'w') as f:
            for sl in statelines:
                f.write('\n'.join(sl))
            f.write('\n')
            
    else:
        for sl in statelines:    
            for line in sl:
                print(line)
        
        
                    
    
    
            
            