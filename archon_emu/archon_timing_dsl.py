#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 22:04:12 2017

@author: danw
"""

import pyparsing as ps
from enum import Enum
from archon_sample_data import *

import logging



 
class ArchonInstructions(Enum):
    STATE = 0
    GOTO = 1
    CALL = 2
    DECREMENT = 3
    RETURN = 4
    CONDITIONAL =5
    
#TODO: NOP

#these instructions represent control flow jumps
CALL_INSTR_TYPES = [ArchonInstructions.CALL , ArchonInstructions.GOTO]

#these instructions can take an loop argument
ARGUMENT_INSTR_TYPES = [ArchonInstructions.CALL, ArchonInstructions.DECREMENT]


litsup = lambda char : ps.Literal(char).suppress()
kwsup = lambda kw : ps.Keyword(kw).suppress()
setparsecall = lambda obj, fun : obj.setParseAction(lambda t : fun(*t))

class ArchonCompiler:
    def __init__(self,states,params,constants):
        self.logger = logging.getLogger('archon_emu.ArchonCompiler')
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
        setparsecall(labeldefine,self.define_label)
        
        state_expr = ps.Or(state_kws)
        setparsecall(state_expr,self.output_state)
        
        GOTO = kwsup('GOTO') + label        
        setparsecall(GOTO,self.goto)
        
        
        RETURN = (kwsup('RETURN') + label)
        setparsecall(RETURN,self.ret)
        
        CALL = (kwsup('CALL') + label + litsup('(') + subroutinearg + litsup(')'))
        setparsecall(CALL,self.call)
        
        IMPLICITCALL = (label + litsup('(') + subroutinearg + litsup(')'))        
        setparsecall(IMPLICITCALL,self.implicitcall)

        #DECREMENT needs to be special cased, not quite sure why
        DECREMENT = ps.Or(parameter_literals) + litsup('--')
        setparsecall(DECREMENT,self.decrement)
        builtin_action =  GOTO ^ DECREMENT ^ CALL ^ IMPLICITCALL ^ RETURN 
        IF = (kwsup('IF') + ps.Optional(ps.Literal('!')) + ps.Or(parameter_kws) + builtin_action.suppress())
        
        #the odd one out!
        IF.setParseAction(lambda t : self.conditional(t))
                
        
        active_timing_line = state_expr + ps.ZeroOrMore(litsup(';') + (builtin_action ^ IF )) 
        active_timing_line.setParseAction(lambda t: self.advance_line())

        archon_dsl_expr = ps.OneOrMore(comment | labeldefine | active_timing_line)
        
        return archon_dsl_expr

    def debug_linenum_msg(self,msg,fun = logging.Logger.debug):
        fun(self.logger, ('line %d: ' % self.linenum) + msg )
        
    def define_label(self,labelname):
        self.labeljumps[labelname] = self.linenum
        self.debug_linenum_msg('defining label: %s' % labelname)
        
    def output_state(self,statename):
        self.currentlineactions.append( (ArchonInstructions.STATE,statename)) 
        self.debug_linenum_msg('setting state: %s ' % ( statename))
            
    def goto(self,labelname):
        self.currentlineactions.append( [ArchonInstructions.GOTO,labelname])
        self.debug_linenum_msg('GOTO: %s' % (self.linenum))
        
    def call(self,labelname,argument=None):
        #deref an integer literal immediately
        try:
            argument = int(argument)
        except ValueError:
            pass
        
        self.currentlineactions.append( [ArchonInstructions.CALL, labelname,argument])
        self.debug_linenum_msg('CALL: %s %s' % (labelname,argument))
    
    def implicitcall(self,labelname,argument=None):
        #implicitly define a subroutine
        #TODO: implicit calls don't work at the moment, need to do something cleverer
        
        #EXPERIMENTAL: define state and return
        # then push a label and call one back
        
        self.define_label(labelname)
        self.ret(labelname,argument)
        
        currstate = self.currentlineactions[0][1]
        prevlineactions = [ [ArchonInstructions.STATE,currstate], 
                           [ArchonInstructions.CALL,labelname]]
        
        print('IMPLICIT CALL: %s %s' % (labelname,argument))
        
        
    def ret(self,labelname):
        self.currentlineactions.append( [ArchonInstructions.RETURN, labelname])
        self.debug_linenum_msg('RETURN: %s' % labelname)
    
    def conditional(self,ts):
        self.debug_linenum_msg('CONDITIONAL')
        if len(ts) > 1:
            #HACK: this implies it has a NOT operator
            tf = False
            val = ts[1]
        else:
            tf = True
            val = ts[0]

        #HACK: conditional needs to go in at the second to last position
        #the last instruction should be the execution of the conditional
        self.currentlineactions.insert(-1, (ArchonInstructions.CONDITIONAL,tf,val))
        
    def decrement(self,t):
        self.currentlineactions.append((ArchonInstructions.DECREMENT, t))
        self.debug_linenum_msg('decrement %s' %t)
        print('DECREMENT')
    
        
    def advance_line(self):
        self.alllineactions.append(self.currentlineactions)
        self.currentlineactions = []
        self.linenum += 1
        self.logger.debug('line increments to %d ' % self.linenum)
        
        

    def check_label_consistency(self):
        #assemble a list of everything that's ever referenced via CALL, GOTO, or RETURN
        all_used_call_targets = []
        
        for line in self.alllineactions:
            calls = [_ for _ in line if _[0] in CALL_INSTR_TYPES]
            for call in calls:
                if call[1] not in all_used_call_targets:
                    all_used_call_targets.append(call[1])
        
        
        for target in all_used_call_targets:
            if target not in self.labeljumps.keys():
                raise IndexError("script calls a label %s which doesn't appear to be defined" % target)
        
    def check_duplicate_params_constants(self):
        duplicates = [_ for _ in self.params.keys() if _ in self.constants.keys()]
        if len(duplicates) > 0:
            raise ValueError('the names %s appear as both a parameter and a constant' % duplicates)

    def dereference_jumps(self):
        for line in self.alllineactions:
            for instr in line:
                if instr[0] in CALL_INSTR_TYPES:
                    #instr[1] will always be the jump target
                    #de-reference the name to a location
                    instr[1] = self.labeljumps[instr[1]]


    def dereference_consts(self):
        for line in self.alllineactions:
            for instr in line:
                if instr[0] in ARGUMENT_INSTR_TYPES:
                    if instr[-1] in self.constants:
                        instr[-1] = self.constants[instr[-1]]
                

    def compile_timing_script(self, script):
        #reset internal state
        self.alllineactions = []
        self.linenum = 0
        self.labeljumps = {}        

        #parse the timing script 
        dsl_expr = self.construct_parser()
        dsl_expr.parseString(script)
    
        #run script checks
        self.check_label_consistency()
        self.check_duplicate_params_constants()
        
        #run compiler "2nd pass"
        self.dereference_jumps()
        self.dereference_consts()
        
        return self.alllineactions
        
if __name__ == '__main__':
    sm = ArchonCompiler(states=sample_states,params=sample_params,constants = sample_constants)    
    
    
    dsl_expr = sm.construct_parser()
    
    parse_results = dsl_expr.parseString(sample_script)
    
    sm.check_label_consistency()
    sm.check_duplicate_params_constants()
    sm.dereference_jumps()
    sm.dereference_consts()