#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 22:18:41 2017

@author: danw
"""

sample_states = {'AllClocksLow' : [0,0,0,0,0],
                 'AllClocksHigh' : [1,1,1,1,1],
                'StateA' : [1,0,0,0,0],
                'StateB' : [0,1,0,0,0],
                'StateC' : [0,0,1,0,0],
                'StateD' : [0,0,0,1,0],
                'StateE' : [0,0,0,0,1]
}

sample_params = {'MyParameter' : 1
                 }

sample_constants = {'MyConstant' : 100
                    }
                 
                 
sample_script = """
# Any line starting with a hash is a comment, and is ignored. Blank lines are also ignored.
# A name followed by a colon is a label, and is used as a target for GOTO, CALL and
# RETURN instructions
MyLabel:
# For any line that is not a label, the first token expected is the name of an output state.
# These output states are defined outside of the script, and declare the state of the
# timing core outputs for this clock cycle (high, low, or no change).
AllClocksLow
# A jump is declared as follows:
AllClocksLow; GOTO MyLabel
# Parameters are also defined outside the script, and are referenced by name.
# To conditionally jump if a parameter is non-zero:
AllClocksLow; IF MyParameter GOTO MyLabel
# To conditionally jump if a parameter is zero:
AllClocksLow; IF !MyParameter GOTO MyLabel
# To call a subroutine 100 times using a direct value, a declared constant or a parameter:
AllClocksLow; CALL MySubroutine(100)
AllClocksLow; CALL MySubroutine(MyConstant)
# MyParameter would have to be set to 100 for the subroutine to execute 100 times.
# If MyParameter is zero, the call will not execute. Constants must be non-zero.
AllClocksLow; CALL MySubroutine(MyParameter)
# All of these CALLs push the next execution address and current active count value to
# the stack, set the active count value to the count provided, and jump to the given address.
# A subroutine that has all clocks high for one clock tick would look like this:
MySubroutine:
AllClocksHigh; RETURN MySubroutine
# The RETURN statement tells the core to decrement the active count. If zero, it pops the
# return address and active count from the stack. If non-zero, it jumps to the provided
# address (executing MySubroutine again).
# It’s often convenient to hold a particular output state for a given number of clock cycles.
# This could be done by defining a subroutine with just one instruction (as in the
# MySubroutine example above) and calling it 100 times. This can also be accomplished
# as follows:
AllClocksHigh; AllClocksHigh(99)
# This implicitly generates a subroutine and calls it – all clocks will be high for 100 clock cycles.
# Here is an example script with output. A timing core with outputs A through E is assumed,
# with a single output high in each state
ExampleStart:
StateA
StateB; CALL ExampleSub(2)
StateE; GOTO ExampleStart
ExampleSub:
StateC; StateC(3)
StateD; RETURN ExampleSub
"""
