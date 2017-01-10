#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 22:04:12 2017

@author: danw
"""

import pyparsing as ps

from archon_sample_data import *


NOP,GOTO,CALL,RETURN = map(ps.Keyword,['NOP','GOTO','CALL','RETURN'])
label = ps.Word(ps.alphas) + ps.Literal(':').suppress()
 



class ArchonStateMachine:
    def __init__(self,states,params,constants):
        self.states = states
        self.params = params
        self.constants = constants
        
        self.time = 0
        
    def compile_parser(self):
        #define keywords recognised within this timing script
        label = ps.Word(ps.alphas)
        parameter_kws = [ps.Keyword(k) for k in self.params.keys()]
        state_kws = [ps.Keyword(k) for k in self.states.keys()]
        constant_kws = [ps.Keyword(k) for k in self.constants.keys()]
                     
        comment  = ps.Literal('#').suppress() + ps.restOfLine.suppress() 
        
        
        labeldefine = (label + ps.Literal(':').suppress() + ps.restOfLine.suppress())
        labeldefine.setParseAction(lambda s,l,t : self.define_label(t[0]))
        
        state_expr = ps.Or(state_kws).setParseAction(lambda s,l,t: self.output_state(t))
        
        GOTO = (ps.Keyword('GOTO').suppress() + label).setParseAction(lambda s,l,t : self.goto(t))
        
        subroutinearg = ps.Word(ps.nums) | ps.Or(parameter_kws) | ps.Or(constant_kws)
        CALL = (ps.Keyword('CALL').suppress() + label + ps.Literal('(').suppress() + subroutinearg + ps.Literal(')').suppress())
        CALL.setParseAction(lambda t: self.call(t))
        
        IMPLICITCALL = (label + ps.Literal('(').suppress() + subroutinearg + ps.Literal(')').suppress())
        IMPLICITCALL.setParseAction(lambda t : self.call(t))
        
        RETURN = (ps.Keyword('RETURN').suppress() + label)
        RETURN.setParseAction(lambda t: self.ret(t))
        
        builtin_action = GOTO | CALL | IMPLICITCALL | RETURN
        
        IF = (ps.Keyword('IF').suppress() + ps.Optional(ps.Literal('!')) + ps.Or(parameter_kws) + builtin_action)
        IF.setParseAction(lambda toks: print('CONDITIONAL' + str(toks)))
        

        active_timing_line = (state_expr + ps.Optional(ps.Literal(';') + (builtin_action | IF))).setParseAction(lambda s,l,t: self.advance_time())

        archon_dsl_expr = ps.OneOrMore(comment | labeldefine | active_timing_line)
        
        return archon_dsl_expr

    def define_label(self,labelname):
        print('defining label: %s' % labelname)

            
    def output_state(self,statename):
        print('setting state: %s ' % statename)
    
        
    def goto(self,labelname):
        print('GOTO: %s' % labelname)
        
    def call(self,labelname):
        print('CALL: %s' % labelname)
        
    def ret(self,labelname):
        print('RETURN: %s' % labelname)
        
    def advance_time(self):
        self.time += 1
        print('time moves on')
        
        


if __name__ == '__main__':
    sm = ArchonStateMachine(states=sample_states,params=sample_params,constants = sample_constants)    
    
    dsl_expr = sm.compile_parser()
    
    dsl_expr.parseString(sample_script)
    