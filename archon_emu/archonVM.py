#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 01:45:15 2017

@author: danw
"""

from .archon_timing_dsl import  CALL_INSTR_TYPES, ARGUMENT_INSTR_TYPES
from .archontypes import ArchonInstructions
#
#class ArchonInstructions(Enum):
#    STATE = 0
#    GOTO = 1
#    CALL = 2
#    DECREMENT = 3
#    RETURN = 4
#    CONDITIONAL =5
#    REPEAT=6


class ArchonVM:
    
    def __init__(self,parameters,clockstates,instrumentation=None):
        self.parameters = parameters
        self.clockstates = clockstates
        if instrumentation is None:
            self.instrument_output=False
        else:
            self.instrumented_derefs = instrumentation[0]
            self.instrumented_calls = instrumentation[1]    
            self.labeljumps = instrumentation[2]
        
        
    def run(self,instructions, start_ptr = 0):
        #setup initial state
        self.time = 0
        self.currentClockState = None
        self.loopcount = 0
        self.instruction_ptr = start_ptr
        self.callstack = []
        self.jumpptr = 0
        self.state = None

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
                print(instr)
                
                if instr[0] is ArchonInstructions.CONDITIONAL:                    
                    paramval = self.deref(instr[2])
                    condition = bool(paramval) if instr[1] else not bool( paramval)
                    if not condition:
                        print('condition not matched')
                        #set the loop to skip over the next instruction
                        skipinstr = True
                elif instr[0] is ArchonInstructions.STATE:
                    print('setting state')
                    self.state = instr[1]
                elif instr[0] is ArchonInstructions.GOTO:
                    print('GOTO')
                    self.jumpptr = instr[1]
                elif instr[0] is ArchonInstructions.CALL:
                    print('CALL')
                    self.jumpptr = instr[1]
                    self.callstack.append(self.instruction_ptr)
                    self.loopcount = self.deref(instr[2])
                elif instr[0] is ArchonInstructions.DECREMENT:
                    print('DECREMENT')
                    self.parameters[instr[1]] -= 1
                elif instr[0] is ArchonInstructions.RETURN:
                    print('RETURN')
                    #return needs higher priority (i.e. further down the block) than
                    #CALL, otherwise implicit call structure doesn't work properly
                    self.loopcount -= 1
                    print('loopcount = %d' % self.loopcount)
                    if self.loopcount <= 0:
                        #jump out of subroutine 
                        self.jumpptr = self.callstack.pop() + 1
                        print('jumping back to %d' % self.jumpptr)
                    else:
                        #jump back to start of subroutine
                        self.jumpptr = instr[1]
            
            yield self.time, self.instruction_ptr,self.state    
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
        
if __name__ == '__main__':
    from archon_sample_data import *
    from archon_timing_dsl import ArchonCompiler
    
    compiler = ArchonCompiler(states=sample_states,params=sample_params,
                              constants=sample_constants)
    
    instructions = compiler.compile_timing_script(sample_script)
    
    vm = ArchonVM({'MyParameter': 1}, sample_states)
    
    it = vm.run(instructions)