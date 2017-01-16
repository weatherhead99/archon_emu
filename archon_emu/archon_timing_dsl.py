#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 22:04:12 2017

@author: danw
"""

import pyparsing as ps
from enum import Enum


import logging

from .archontypes import ArchonInstructions   
    
#TODO: NOP
#TODO: HANDLE EMPTY LINES

#these instructions represent control flow jumps
CALL_INSTR_TYPES = [ArchonInstructions.CALL , ArchonInstructions.GOTO, ArchonInstructions.RETURN]

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
        self.instrumented_derefs = []
        self.instrumented_calls = []

        self.aux_instrumented_calls = []
        self.aux_instrumented_derefs = []
        self.auxlines =[]
        self.auxlabeljumps = {}
        self.auxlinenum = 0

        self.commentlines = []
            
    def construct_parser(self):
        #define keywords recognised within this timing script
        label = ps.Word(ps.alphanums)
        parameter_kws = [ps.Keyword(_) for _ in self.params]
        parameter_literals = [ps.Literal(_) for _ in self.params]
        state_kws = [ps.Keyword(_) for _ in self.states]
        constant_kws = [ps.Keyword(_) for _ in self.constants]
        subroutinearg = ps.Word(ps.nums) | ps.Or(parameter_kws) | ps.Or(constant_kws)

        #comments are completely ignored by the parser, not even assigned to a line number
        comment  = litsup('#') + ps.restOfLine.suppress() 
        setparsecall(comment,self.comment)
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
        
        CALL = (kwsup('CALL') + label + ps.Optional(litsup('(') + subroutinearg + litsup(')')))
        setparsecall(CALL,self.call)
        
        IMPLICITCALL = (label + litsup('(') + subroutinearg + litsup(')'))        
        setparsecall(IMPLICITCALL,self.implicitcall)

        #DECREMENT needs to be special cased, not quite sure why
        DECREMENT = ps.Or(parameter_literals) + litsup('--')
        setparsecall(DECREMENT,self.decrement)
        
        IF = (kwsup('IF') + ps.Optional(ps.Literal('!')) + ps.Or(parameter_kws)  )
        #TODO: WHAT HAPPENS ON IF + STATENAME?????
        
        #the odd one out!
        IF.setParseAction(lambda t : self.conditional(t))
        
        
        builtin_action =  CALL ^ GOTO ^ DECREMENT ^ IMPLICITCALL ^ RETURN 
        #IF = (kwsup('IF') + ps.Optional(ps.Literal('!')) + ps.Or(parameter_kws) + builtin_action.suppress())
                
        
        active_timing_line = state_expr + ps.ZeroOrMore(litsup(';') + (builtin_action ^ (IF + (builtin_action^ state_expr)))) + ps.Optional(litsup(';')) 
        active_timing_line.setParseAction(lambda t: self.advance_line())

        archon_dsl_expr = ps.OneOrMore(comment | labeldefine | active_timing_line)
        
        return archon_dsl_expr

    def debug_linenum_msg(self,msg,fun = logging.Logger.debug):
        fun(self.logger, ('line %d: ' % (self.linenum +1) + msg ))

    def comment(self):
        self.commentlines.append(self.linenum)
        self.debug_linenum_msg('line %d is a comment' % self.linenum)
        
    def define_label(self,labelname):
        self.labeljumps[labelname] = self.linenum
        self.debug_linenum_msg('defining label: %s' % labelname)
        
    def output_state(self,statename):
        self.currentlineactions.append( [ArchonInstructions.STATE,statename]) 
        self.debug_linenum_msg('setting state: %s ' % ( statename))
            
    def goto(self,labelname):
        self.currentlineactions.append( [ArchonInstructions.GOTO,labelname])
        self.debug_linenum_msg('GOTO: %s' % (self.linenum))
        
    def call(self,labelname,argument=None):
        #deref an integer literal immediately
        if argument is None:
            argument = 1
        try:
            argument = int(argument)
        except ValueError:
            pass
        
        self.currentlineactions.append( [ArchonInstructions.CALL, labelname,argument])
        self.debug_linenum_msg('CALL: %s %s' % (labelname,argument))
    
    def implicitcall(self,labelname,argument=None):        
        self.currentlineactions.append([ArchonInstructions.CALL,labelname,argument])
        
        auxline = [  [ArchonInstructions.STATE,labelname],
                    [ArchonInstructions.RETURN,labelname]]
        
        self.auxlines.append(auxline)
        self.auxlabeljumps[labelname] = self.auxlinenum
        self.auxlinenum += 1
        
        self.aux_instrumented_derefs.append([])
        self.aux_instrumented_calls.append([])

        
    def ret(self,labelname):
        self.currentlineactions.append( [ArchonInstructions.RETURN, labelname])
        self.debug_linenum_msg('RETURN: %s' % labelname)
    
    def conditional(self,ts):                
        if len(ts) > 1:
            #HACK: this implies it has a NOT operator
            tf = False
            val = ts[1]
            self.debug_linenum_msg('CONDITIONAL on parameter %s being FALSE' % str(val) )
            
        else:
            tf = True
            val = ts[0]
            self.debug_linenum_msg('CONDITIONAL on parameter %s being TRUE' % str(val) )

        #HACK: conditional needs to go in at the second to last position
        #the last instruction should be the execution of the conditional
        self.currentlineactions.append( [ArchonInstructions.CONDITIONAL,tf,val])
        
    def decrement(self,t):
        self.currentlineactions.append((ArchonInstructions.DECREMENT, t))
        self.debug_linenum_msg('decrement %s' %t)
#        print('DECREMENT')
    
        
    def advance_line(self):
        self.alllineactions.append(self.currentlineactions)
        self.currentlineactions = []
        self.linenum += 1
        self.logger.debug('line increments to %d ' % (self.linenum +1))
        
        self.instrumented_derefs.append([])
        self.instrumented_calls.append([])
        
    def check_script_length(self):
        pass

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
        for ind,line in enumerate(self.alllineactions):
            for instr in line:
                if instr[0] in CALL_INSTR_TYPES:
                    #instr[1] will always be the jump target
                    #de-reference the name to a location
                    labelname = instr[1]
                    instr[1] = self.labeljumps[labelname]

                    #append the name we just replaced, for instrumentation purposes
                    self.instrumented_calls[ind].append(labelname)


    def dereference_consts(self):
        for ind,line in enumerate(self.alllineactions):
            for instr in line:
                if instr[0] in ARGUMENT_INSTR_TYPES:
                    if instr[-1] in self.constants:
                        constname = instr[-1]
                        instr[-1] = self.constants[constname]
                        self.instrumented_derefs[ind].append(constname)
                        #append constant name for instrumentation purposes
                        
    def get_instrumentation(self):
        return [self.instrumented_derefs,self.instrumented_calls,self.labeljumps]

    def compile_timing_script(self, script,forcecompile=True):
        #reset internal state
        self.alllineactions = []
        self.linenum = 0
        self.labeljumps = {}        

        #parse the timing script 
        dsl_expr = self.construct_parser()
        
        if forcecompile:
            dsl_expr += ps.StringEnd()
        
        try:
            dsl_expr.parseString(script)
        except ps.ParseException:
            raise RuntimeError("couldn't parse script beyond line %d, this could be an archon_emu bug" % self.linenum)
        
        #add a halt instruction
        self.currentlineactions.append([ArchonInstructions.HALT])
        self.advance_line()
        
        #merge implicit calls
        self.alllineactions.extend(self.auxlines)
        #merge implicit call labels
        implicit_labels_with_offsets = {k:v+self.linenum for k,v in self.auxlabeljumps.items()}
        self.labeljumps.update(implicit_labels_with_offsets)
    
        #merge implicit instrumented stuff
        self.instrumented_derefs.extend(self.aux_instrumented_derefs)
        self.instrumented_calls.extend(self.aux_instrumented_calls)
        
        #run script checks
        print('comments: %s')
        self.check_label_consistency()
        self.check_duplicate_params_constants()
        
        #run compiler "2nd pass"
        self.dereference_jumps()
        self.dereference_consts()
        
        return self.alllineactions
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    from archon_sample_data import *
    params = {'Tsf' : 100000}
    states = ['KEEPER']

    sm = ArchonCompiler(states=states,params=params,constants = sample_constants)    
    
    
    
    dsl_expr = sm.construct_parser()
    
    testscript = """MyLabel:
    AllClocksLow; IF !MyParameter GOTO MyLabel"""
    
    testscript2 = """SF1;SF1(Tsf)"""
    
    parse_results = dsl_expr.parseString(testscript2)

    
    sm.check_label_consistency()
    sm.check_duplicate_params_constants()
    sm.dereference_jumps()
    sm.dereference_consts()