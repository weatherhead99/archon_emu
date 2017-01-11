#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 22:04:12 2017

@author: danw
"""

import pyparsing as ps
from enum import Enum
from archon_sample_data import *


NOP,GOTO,CALL,RETURN = map(ps.Keyword,['NOP','GOTO','CALL','RETURN'])
label = ps.Word(ps.alphas) + ps.Literal(':').suppress()
 
class ArchonInstructions(Enum):
    STATE = 0
    GOTO = 1
    CALL = 2
    DECREMENT = 3
    RETURN = 4
    CONDITIONAL =5
    DEREF = 6



litsup = lambda char : ps.Literal(char).suppress()
kwsup = lambda kw : ps.Keyword(kw).suppress()
setparsecall = lambda obj, fun : obj.setParseAction(lambda t : fun(*t))

class ArchonStateMachine:
    def __init__(self,states,params,constants):
        self.states = states
        self.params = params
        self.constants = constants
        self.linenum = 0
        self.labeljumps = {}
        self.currentlineactions = []
        self.alllineactions = []
            
    def construct_parser(self):
        #define keywords recognised within this timing script
        label = ps.Word(ps.alphas)
        parameter_kws = [ps.Keyword(_) for _ in self.params]
        parameter_literals = [ps.Literal(_) for _ in self.params]
        state_kws = [ps.Keyword(_) for _ in self.states]
        constant_kws = [ps.Keyword(_) for _ in self.constants]
        subroutinearg = ps.Word(ps.nums) | ps.Or(parameter_kws) | ps.Or(constant_kws)

        #comments are completely ignored by the parser, not even assigned to a line number
        comment  = litsup('#') + ps.restOfLine.suppress() 
        
        #the following work in a "standard" way, just call a member function with the first 
        #parsed token
        labeldefine = (label + litsup(':') + ps.restOfLine.suppress())        
        state_expr = ps.Or(state_kws)
        GOTO = kwsup('GOTO') + label        
        DECREMENT = (ps.Or(parameter_literals) + litsup('--'))        
        RETURN = (kwsup('RETURN') + label)
        CALL = (kwsup('CALL') + label + litsup('(') + subroutinearg + litsup(')'))
        
        IMPLICITCALL = (label + litsup('(') + subroutinearg + litsup(')'))        
        builtin_action = GOTO | CALL | IMPLICITCALL | DECREMENT | RETURN
        IF = (kwsup('IF') + ps.Optional(ps.Literal('!')) + ps.Or(parameter_kws) + builtin_action.suppress())

        #TOOLATETOFIGUREOUT: why doesn't this work in a for loop?        
        setparsecall(labeldefine,self.define_label)
        setparsecall(state_expr,self.output_state)
        setparsecall(GOTO,self.goto)
        setparsecall(DECREMENT,self.decrement)
        setparsecall(RETURN,self.ret)
        setparsecall(CALL,self.call)
        setparsecall(IMPLICITCALL,self.implicitcall)
        
        #the odd one out!
        IF.setParseAction(lambda t : self.conditional(t))
                
        active_timing_line = (state_expr + ps.Optional(litsup(';') + (builtin_action | IF)))
        active_timing_line.setParseAction(lambda t: self.advance_line())

        archon_dsl_expr = ps.OneOrMore(comment | labeldefine | active_timing_line)
        
        return archon_dsl_expr

        
    def define_label(self,labelname):
        print('defining label: %s' % labelname)
        self.labeljumps[labelname] = self.linenum
        

            
    def output_state(self,statename):
        self.currentlineactions.append( (ArchonInstructions.STATE,statename)) 
        print('setting state: %s ' % statename)
    
        
    def goto(self,labelname):
        self.currentlineactions.append( (ArchonInstructions.GOTO,labelname))
        print('GOTO: %s' % labelname)
        
    def call(self,labelname,argument=None):
        self.currentlineactions.append( (ArchonInstructions.CALL, labelname,argument))
        print('CALL: %s %s' % (labelname,argument))
    
    def implicitcall(self,labelname,argument=None):
        print('IMPLICIT CALL: %s %s' % (labelname,argument))
    
    def ret(self,labelname):
        self.currentlineactions.append( (ArchonInstructions.RETURN, labelname))
        print('RETURN: %s' % labelname)
    
    def conditional(self,ts):
        print('CONDITIONAL')
        print(ts)
        if len(ts) > 1:
            #HACK: this implies it has a NOT operator
            tf = False
            val = ts[1]
        else:
            tf = True
            val = ts[0]
            
        self.currentlineactions.append( (ArchonInstructions.CONDITIONAL,tf,val))
        
    def decrement(self,t):
        self.currentlineactions.append((ArchonInstructions.DECREMENT, t))
        print('decrement %s' %t)
    
        
    def advance_line(self):
        self.alllineactions.append(self.currentlineactions)
        self.currentlineactions = []
        self.linenum += 1
        print('line increments to %d ' % self.linenum)
        
        

    def check_label_consistency(self):
        #assemble a list of everything that's ever referenced via CALL, GOTO, or RETURN
        all_used_call_targets = []
        CALL_INSTR_TYPES = [ArchonInstructions.CALL , ArchonInstructions.GOTO,
                            ArchonInstructions.RETURN]

        for line in self.alllineactions:
            calls = [_ for _ in line if _[0] in CALL_INSTR_TYPES]
            for call in calls:
                if call[1] not in all_used_call_targets:
                    all_used_call_targets.append(call[1])
        
        print(all_used_call_targets)
        for target in all_used_call_targets:
            if target not in self.labeljumps.keys():
                raise IndexError("script calls a label %s which doesn't appear to be defined" % target)
        
    def check_duplicate_params_constants(self):
        duplicates = [_ for _ in self.params.keys() if _ in self.constants.keys()]
        if len(duplicates) > 0:
            raise ValueError('the names %s appear as both a parameter and a constant' % duplicates)

if __name__ == '__main__':
    sm = ArchonStateMachine(states=sample_states,params=sample_params,constants = sample_constants)    
    
    dsl_expr = sm.construct_parser()
    
    dsl_expr.parseString(sample_script)
    
    sm.check_label_consistency()
    sm.check_duplicate_params_constants()