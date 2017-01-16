#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 14:03:12 2017

@author: danw
"""
import warnings
import logging
from archon_emu.acffile import ArchonConfig, StateConfigWarning
from archon_emu.archon_timing_dsl import ArchonCompiler
from archon_emu.archonVM import ArchonVM, ArchonVM_Instrumented

def print_timing_script(conf):
    print(conf.timing_script.encode('ASCII').decode('unicode_escape'))    

if __name__ =='__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    warnings.simplefilter('ignore',category=StateConfigWarning)
    
    
    fl = 'seqs/CCD250_20161109_LOW_GAIN-reversed-xed.acf'
    fl2 = 'seqs/CCD250_e2v_Image.acf'
    fl3 = 'seqs/CCD250_e2v_MeanVar.acf'
    
    archon_conf = ArchonConfig.from_filename(fl)
    compiler = ArchonCompiler.from_archonconfig(archon_conf)
    vm = ArchonVM.from_compiler(compiler)
    
    #BUG: currently can't use a compiler object twice


    it = vm.run()
    
    #pull some states out
    
        
    
    