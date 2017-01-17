#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 01:45:15 2017

@author: danw
"""

from .archon_timing_dsl import  CALL_INSTR_TYPES, ARGUMENT_INSTR_TYPES
from .archontypes import ArchonInstructions
from .archon_timing_dsl import ArchonCompiler
import logging

class ArchonVM:
    @classmethod
    def from_compiler(cls,obj):
        if isinstance(obj,ArchonCompiler):
            instructions = obj.compile_timing_script()
            return cls(obj.params,obj.states,instructions)
        raise TypeError("don't know how to construct a %s from a %s" % (cls.__name__, type(obj).__name__))
            
    
    def __init__(self,parameters,clockstates,instructions=None):
        self.parameters = parameters
        self.clockstates = clockstates
        if instructions is not None:
            self.instructions = instructions
            
        self.logger = logging.getLogger('archon_emu.ArchonVM')
    
    def debug_iptr_msg(self,msg,fun = logging.Logger.debug):
        fun(self.logger, ('iptr %d: %s' %(self.instruction_ptr, msg)))
        
    def run(self,instructions=None, start_ptr = 0):
        if instructions is None:
            instructions = self.instructions
        #setup initial state
        self.time = 0
        self.currentClockState = None
        self.loopcount = 0
        self.instruction_ptr = start_ptr
        self.callstack = []
        self.jumpptr = start_ptr


        while(self.instruction_ptr < len(instructions)):
            current_instructions = instructions[self.instruction_ptr]            
            
            #some things we don't know about DECREMENT
            #1) is IF MyParameter; MyParameter-- a valid Archon construct?
            #2) is State; CALL MySub(MyParameter); MyParameter-- a valid construct?
            #3) if 2, what does it do?
            
            #compiler should output instructions in correct order
            
            #unless changed later, the next time step we do the next set of instructions
            self.jumpptr = self.instruction_ptr+1
            skipinstr = False
            
            for instr in current_instructions:
                if(skipinstr):
                    skipinstr = False
                    continue
#                self.debug_iptr_msg(instr)
                
                if instr[0] is ArchonInstructions.CONDITIONAL:                    
                    paramval = self.deref(instr[2])
                    condition = bool(paramval) if instr[1] else not bool( paramval)
                    self.debug_iptr_msg('CONDITIONAL on %s' % str(instr[2]))
                    if not condition:
                        self.debug_iptr_msg('condition not matched')
                        #set the loop to skip over the next instruction
                        skipinstr = True
                elif instr[0] is ArchonInstructions.STATE:
                    self.debug_iptr_msg('setting state %s' % instr[1])
                    self.currentClockState = instr[1]
                elif instr[0] is ArchonInstructions.GOTO:
                    self.debug_iptr_msg('GOTO: %d' %instr[1])
                    self.jumpptr = instr[1]
                elif instr[0] is ArchonInstructions.CALL:
                    self.debug_iptr_msg('CALL: %d ' % instr[1] + str(instr[2]))
                    self.jumpptr = instr[1]
                    self.callstack.append(self.instruction_ptr)
                    self.loopcount = self.deref(instr[2])
                elif instr[0] is ArchonInstructions.DECREMENT:
                    self.debug_iptr_msg('DECREMENT %s'  % instr[1])
                    self.parameters[instr[1]] -= 1
                elif instr[0] is ArchonInstructions.RETURN:
                    self.debug_iptr_msg('RETURN')
                    #return needs higher priority (i.e. further down the block) than
                    #CALL, otherwise implicit call structure doesn't work properly
                    self.loopcount -= 1
                    self.debug_iptr_msg('loopcount = %d' % self.loopcount)
                    if self.loopcount <= 0:
                        #jump out of subroutine 
                        self.jumpptr = self.callstack.pop() + 1
                        self.debug_iptr_msg('jumping back to %d' % self.jumpptr)
                    else:
                        #jump back to start of subroutine
                        self.jumpptr = instr[1]
            
            yield self.time, self.instruction_ptr,self.currentClockState
            self.instruction_ptr = self.jumpptr
            self.time += 1
            
            
    def deref(self,val):
        val = val if type(val) is int else self.parameters[val]
        return val
            
        
    
    def _pushstack(self,ptr):
        pass
    
    def _popstack(self):
        pass
    
    def applyclockstate(self,state):
        print('applying %s ' % state)


class ArchonVM_Instrumented(ArchonVM):
    @classmethod
    def from_compiler(cls,obj):
        if isinstance(obj,ArchonCompiler):
            instructions = obj.compile_timing_script()
            instrumentation = obj.get_instrumentation()
            return cls(obj.params,obj.states,instrumentation,instructions)
        raise TypeError("don't know how to construct a %s from a %s" % (cls.__name__, type(obj).__name__))
    
    def __init__(self,parameters,clockstates,instrumentation,instructions=None):
        super().__init__(parameters,clockstates,instructions)
        self.instrumented_derefs = instrumentation[0]
        self.instrumented_calls = instrumentation[1]    
        self.labeljumps = instrumentation[2]
        self.reverse_lookup_labeljumps = {v:k for k,v in self.labeljumps.items()}
        
    def run(self,instructions=None,start_ptr =0 ):
        baseit = super().run(instructions,start_ptr)
        while True:
            time,iptr,statename = next(baseit)
            
            derefs = self.instrumented_derefs[iptr]
            calls = self.instrumented_calls[iptr]
            infun = self.infunc(iptr)
            callstack_infun = [self.infunc(_) for _ in self.callstack]
            
            yield time,iptr,statename,derefs,calls,infun,callstack_infun

            
    def infunc(self,iptr):
        it = iter(sorted(self.reverse_lookup_labeljumps.keys()))
        
        lowbound = next(it)
        while True:
            highbound = next(it)
            if lowbound <= iptr and highbound > iptr:
                return self.reverse_lookup_labeljumps[lowbound]
            lowbound = highbound
            highbound = next(it)
            

        
if __name__ == '__main__':
    from archon_sample_data import *
    from archon_timing_dsl import ArchonCompiler
    
    compiler = ArchonCompiler(states=sample_states,params=sample_params,
                              constants=sample_constants)
    
    instructions = compiler.compile_timing_script(sample_script)
    
    vm = ArchonVM({'MyParameter': 1}, sample_states)
    
    it = vm.run(instructions)
    
        