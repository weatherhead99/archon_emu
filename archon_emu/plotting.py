#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 00:01:52 2017

@author: danw
"""

import matplotlib.pyplot as plt

def simple_plot_clock_sequence(ax,clocks,labels,times=None,offsets=None):
    #"flip' matrix
    clocktranspose = [ [_[i] for _ in clocks]  for i in range(len(clocks[0]))]
    allmax= max(max(_) for _ in clocktranspose)    
    offset = allmax + 1
    for ind,(ct,l) in enumerate(zip(clocktranspose,labels)):        
        yvals = [_ + offset*ind + 1 for _ in ct]
        ax.plot(yvals )
        
    #setup ticks
    yticklocs = [offset * (ind +0.5) + 1 for ind in range(len(clocktranspose))]
    ax.set_yticks(yticklocs)
    ax.set_yticklabels(labels)

if __name__ == '__main__':
    from archon_emu.acffile import ArchonConfig, StateConfigWarning
    from archon_emu.archon_timing_dsl import ArchonCompiler
    from archon_emu.archonVM import ArchonVM
    import warnings
    from itertools import tee
    from archon_emu.archonSM import ArchonSM, filterclocks
    
    warnings.simplefilter('ignore',category=StateConfigWarning) 
    
    f2 = '../seqs/CCD250_e2v_Image.acf'
    
    conf = ArchonConfig.from_filename(f2)
    compiler = ArchonCompiler.from_archonconfig(conf)
    vm = ArchonVM.from_compiler(compiler)
    
    sm = ArchonSM(conf.states,conf.modules,conf.constants, vm)
    #setup some parameters to be a bit quicker
    vm.parameters['LCLK'] = 1
    vm.parameters['Nclear'] = 0
    vm.parameters['PixSkip'] = 0
    vm.parameters['Tpa'] = 1
    vm.parameters['Tpb'] = 1
    

#    spec = {10: [False,True,False,True,False,True,False,True]}

    spec = {10: [False,False,True,False,True,False,True,False]}
    filtergen = filterclocks(sm.clock(vm.run()),spec,flat=True)
    
    clocks = [next(filtergen) for i in range(300)]
    labels=['S1', 'S2', 'S3']

    fig,ax = plt.subplots(1,1)
    
    p = simple_plot_clock_sequence(ax,clocks,labels)