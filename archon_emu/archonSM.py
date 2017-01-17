#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 21:14:17 2017

@author: danw
"""
from archon_emu.archontypes import archon_module_type,ClockState

module_clock_numbers = {archon_module_type.AD : (1,bool),
                        archon_module_type.Driver : (8,float),
                        archon_module_type.LVBias : (8,bool),
                        archon_module_type.LVXBias : (8,bool),
                        archon_module_type.Heater : (8,bool),
                        archon_module_type.HeaterX : (8,bool)
                        }

                        
def deref_val(v,constants,params):
    if v in params:
        return params[v]
    elif v in constants:
        return constants[v]
    return v
                        
class ArchonSM:
    
    def __init__(self,states,modules,constants,vm,initclocks=None):
        self.states = states
        self.modules = modules
        self.constants = constants
        self.vm = vm

        self.clockvals = self._setup_modules()
        if initclocks is not None:
            self.clockvals.add(initclocks)
        
        self._validate_modules()

    def _setup_modules(self):
        mod_numbers = {_.position : [module_clock_numbers[_.type][1]()] * module_clock_numbers[_.type][0] for _ 
                       in self.modules if _.type in module_clock_numbers}

        return mod_numbers
        
    def _validate_modules(self):
        for installedmod in self.modules:
            
            try:
                clocks = self.clockvals[installedmod.position]
            except KeyError as err:
                if installedmod.position in module_clock_numbers:
                    raise KeyError('installed module %d is not configured in SM' % installedmod.position)
                else:
                    continue
                
            if installedmod.type not in module_clock_numbers:
                raise NotImplementedError("haven't implemented clocks for this type of module: %s" % installedmod.type)
                
            if len(clocks) !=  module_clock_numbers[installedmod.type][0]:
                print(len(clocks))
                raise IndexError("mismatched number of clocks setup for module in position %d " % modpos)
            
    def _setup_clock_states(self,initstates = None):
        if initstates is None:
            pass
            
    def resolve_clock_values(self, oldvalues, newvalues):
        cmp = lambda n,o : n if n is not None else o 
        out = [cmp(n,o)  for n,o in zip(newvalues,oldvalues)]
        return out
        
    def clock(self,gen):
        while True:
            statename = next(gen)[2] #should be either (time,iptr,statename) or  (time,iptr,statename,derefs,calls,infun,callstack_infun)
        
            if statename not in self.states:
                raise ValueError('got a state name %s that is not in the SM!' % state[2])
        
            state = self.states[statename]
            #now update internal clock values
            for modpos, modstate in state.items():
                if not isinstance(modstate,ClockState):
                    raise TypeError('invalid type %s for module %d in state %s' % (type(modstate), modpos, statename))
            
                newvals = modstate.get()
                #dereference any parameters
                newvals_derefed = [deref_val(_,self.constants,self.vm.parameters) for _ in newvals]            
                                   
#                if modpos == 10:
#                    print(id(modstate))
#                    print('statename: %s' % statename)
#                    print('oldvalues: %s' % str(self.clockvals[modpos]))
#                    print('newvalues: %s' % str(newvals_derefed))
#                    print('newvalues: %s' % str(newvals))
#                                   
                self.clockvals[modpos] = self.resolve_clock_values(self.clockvals[modpos], newvals_derefed)
            
            yield self.clockvals

def filterclocks(gen,spec,flat=False):
    while True:
        allclocks = next(gen)
        selected_clocks = {k:[_ for ind,_ in enumerate(v) if spec[k][ind]]
                               for k,v in allclocks.items() if k in spec}

        if not flat:
            yield selected_clocks
        else:
            flat_clocks = []
            for v in selected_clocks.values():
                flat_clocks.extend(v)

            yield flat_clocks
    
if __name__ =='__main__':
    from archon_emu.acffile import ArchonConfig, StateConfigWarning
    from archon_emu.archon_timing_dsl import ArchonCompiler
    from archon_emu.archonVM import ArchonVM
    import warnings
    from itertools import tee
    
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
    

    #might want two "copies" of the VM generator
    from itertools import tee
    vmgen,smgen = tee(vm.run())
    
    clockgen = sm.clock(smgen)
    #let's watch what module 10's clocks do
    for i in range(13):
        #print(next(vmgen))
        print(str(next(vmgen)[2]) + '\t' + str(next(clockgen)[10]))
    
    spec = {10: [False,True,False,True,False,True,False,True]}
    filtergen = filterclocks(sm.clock(vm.run()),spec,flat=True)
    
    for i in range(13):
        print(next(filtergen))

