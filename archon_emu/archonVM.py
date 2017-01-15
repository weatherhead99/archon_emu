#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 01:45:15 2017

@author: danw
"""

from archon_timing_dsl import ArchonInstructions, CALL_INSTR_TYPES, ARGUMENT_INSTR_TYPES


class ArchonVM:
    def __init__(self,parameters,clockstates):
        self.parameters = parameters
        self.clockstates = clockstates
        
        
    def run(self,instructions, start_ptr = 0):
        #setup initial state
        self.time = 0
        self.currentClockState = None
        self.loopcount = 0
        self.instruction_ptr = start_ptr
        self.callstack = []
        while(self.instruction_ptr < len(instructions)):
            current_instructions = instructions[self.instruction_ptr]            
            
            #some things we don't know about DECREMENT
            #1) is IF MyParameter; MyParameter-- a valid Archon construct?
            #2) is State; CALL MySub(MyParameter); MyParameter-- a valid construct?
            #3) if 2, what does it do?

            if current_instructions[0][0] is not ArchonInstructions.STATE:
                raise TypeError('Always Expect STATE as first opcode of compiled instruction')
        
            self.currentClockState = current_instructions[0][1]
            yield (self.instruction_ptr, self.time, self.currentClockState)
            
            
            #process variable decrement
            try:
                decrementinstridx = [_[0] is ArchonInstructions.DECREMENT for _ in current_instructions].index(True)
                decrementvar = current_instructions[decrementinstridx][1]
                self.parameters[decrementvar] -= 1    
            except ValueError:
                #this instruction doesn't decrement anything
                pass

            
            #process conditional
            try:
                condinstridx = [_[0] is ArchonInstructions.CONDITIONAL for _ in current_instructions].index(True)
                #dereference parameter from store
                paramval = self.parameters[current_instructions[condinstridx][2]]
                #process the !
                #WARNING: THIS MIGHT BE THE WRONG WAY ROUND!
                condition = not bool(paramval) if current_instructions[condinstridx][1] else bool(paramval)
                
                if condition:
                    #do not check jumps or anything, just increment time and iptr
                    self.instruction_ptr += 1
                    self.time += 1
                    continue
                
            except ValueError:
                pass
            
            #process CALLs, GOTOs and RETURNs
            try:
                jumpinstridx = [_[0] in CALL_INSTR_TYPES for _  in current_instructions].index(True)
                
                if current_instructions[jumpinstridx][0] is ArchonInstructions.GOTO:
                    #nothing else to do, will just jump appropriately
                    self.instruction_ptr = current_instructions[jumpinstridx][1]
                    
                elif current_instructions[jumpinstridx][0] is ArchonInstructions.CALL:
                    #set the count variable, push current instructionptr to stack and then jump
                    countvalue = current_instructions[jumpinstridx][2]
                    if type(countvalue) is not int:
                        #if it's not already an integer, try to dereference it from parameters
                        countvalue = self.parameters[countvalue]
                    self.callstack.append(self.instruction_ptr)
                    self.loopcount = countvalue
                    self.instruction_ptr = current_instructions[jumpinstridx][1]

                elif current_instructions[jumpinstridx][0] is ArchonInstructions.RETURN:
                    #if we've run out of count, pop the stack and go back
                    if self.loopcount == 0 :
                        self.instruction_ptr = self.callstack.pop()    
                    #if we haven't, jump to the value handily encoded in the RETURN stmt
                    else:
                        self.loopcount -=1
                        self.instruction_ptr = current_instructions[jumpinstridx][1]
                    
                
            except ValueError:
                #no jump in this instruction
                self.instruction_ptr += 1
                pass
            
            #time always passes
            self.time += 1

            
            
            
            
    def applyclockstate(self,state):
        print('applying %s ' % state)
        
if __name__ == '__main__':
    from archon_sample_data import *
    from archon_timing_dsl import ArchonCompiler
    
    compiler = ArchonCompiler(states=sample_states,params=sample_params,
                              constants=sample_constants)
    
    instructions = compiler.compile_timing_script(sample_script)
    
    vm = ArchonVM(sample_params, sample_states)
    
    gen = vm.run(instructions)
    
    for i in range(100):
        iptr,time,state =next(gen)
        print('location: %d, time: %d, state: %s' % (iptr,time,state))
        print('loop counter: %d' % vm.loopcount)
        