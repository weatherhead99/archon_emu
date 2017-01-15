#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 18:19:22 2017

@author: weatherill
"""

from collections import namedtuple
from functools import wraps
from configparser import ConfigParser
from enum import Enum
import warnings

class archon_module_type(Enum):
    NONE = 0
    Driver = 1
    AD  = 2
    LVBias = 3
    HVBias = 4
    Heater = 5
    HeaterX = 6 #TODO: this is probably right but not in manual
    HS = 7
    HVXBias = 8
    LVXBias = 9
    LVDS = 9
    
archon_module = namedtuple('module',['position','type','rev','version','id'])
archon_version_string = namedtuple('version',['major','minor','build'])

def firsttime(fun):
    @wraps(fun)
    def f(self):
        if not hasattr(self,'_'+fun.__name__):
            print('firsttime_calculate')
            setattr(self,'_'+fun.__name__,fun(self))
        return getattr(self,'_'+fun.__name__)
    return f

def getnumfromconfig(linename):
    def wrapper(fun):
        @wraps(fun)
        def f(self):
            n = self.cp['CONFIG'].getint(linename)
            return fun(self,n)
        return f
    return wrapper
    
def valparse(val,empty_is_none=False):
    try:
        v = float(val) if '.' in val else int(val)
        return v
    except ValueError:
        if empty_is_none and  len(val) ==0:
            return None
        return val
    
def defparse(line):
    name,val = line.split('=')
    return name, valparse(val)

def versparse(versionstr):
    return archon_version_string(*versionstr.split('.'))

def listparse(lst):
    return (valparse(_,True) for _ in lst.split(','))
    
def stripline(line):
    #strip quotes
    if line.startswith('"') and line.endswith('"'):
        line =  line[1:-1]

    #strip trailing comments
    if '#' in line:
        line = line [:line.index('#')]
    
    #strip tabs: no unicode encoding means this shows up as double backslash
    return line.strip('\\t')


def process_empty(linegen,yieldval=False):
    while True:
        line = next(linegen)
        if len(line) == 0:
            if yieldval:
                yield None
            else:
                continue
        yield line

class StateConfigWarning(Warning):
    pass
        
class NoStateModuleConfig(StateConfigWarning):
    pass

class NoStateControlConfig(StateConfigWarning):
    pass        

class acffile:
    def __init__(self,fname):
        self.cp = ConfigParser()
        self.cp.read(fname)
        
        #some system parameters
        self.backplane_type = ['X4','X12'][self.cp['SYSTEM'].getint('BACKPLANE_TYPE')-1]
        self.backplane_id = self.cp['SYSTEM']['BACKPLANE_ID']
        self.backplane_rev = chr(65 + self.cp['SYSTEM'].getint('BACKPLANE_REV'))
        self.backplane_version = versparse(self.cp['SYSTEM']['BACKPLANE_VERSION'])

    def _extractlines(self,name,nlines,config = None):
        if config is None:
            config=  self.cp['CONFIG']
        return process_empty(stripline(config[name+"%d" % _]) for _ in range(nlines) )
            

        
        
    @property
    @firsttime
    @getnumfromconfig('LINES')
    def timing_script(self,nlines):        
        return list(self._extractlines('LINE',nlines))
        
    @property
    @firsttime
    def modules(self):
        modbitfield = int(self.cp['SYSTEM']['MOD_PRESENT'],16)
        positions_occupied = [bool( (1 << _) & modbitfield ) for _ in range(12)]
        mods_installed = [ind+1 for ind,val in enumerate(positions_occupied) if val is True]
        
        modules = []
        for modind in mods_installed:
            modd = 'MOD%d_' % modind
            tp = archon_module_type(self.cp['SYSTEM'].getint(modd + 'TYPE'))
            rev = chr(65 + self.cp['SYSTEM'].getint(modd + 'REV'))
            vers = versparse(self.cp['SYSTEM'][modd + 'VERSION'])
            idn = self.cp['SYSTEM'][modd + 'ID']                            
            modules.append(archon_module(modind,tp,rev,vers,idn))
        return modules
    
    @property
    @firsttime
    @getnumfromconfig('STATES')
    def states(self,nstates):
        modpos = [_.position for _ in self.modules]
        states = {}
        for stateidx in range(nstates):
            stated = 'STATE%d\\' % stateidx
            name = self.cp['CONFIG'][stated + 'NAME' ]
            #TODO: is a STATEn\CONTROL entry required for all states?
            try:
                control = self.cp['CONFIG'][stated + 'CONTROL']
            except KeyError:
                warnings.warn("state %d doesn't have a 'CONTROL' subkey" % stateidx,
                              NoStateControlConfig)
            
            modstates = {}

            for modind in modpos:
                modd = 'MOD%d' % modind
                try:
                    modstates[modind] = list(listparse(
                                stripline(self.cp['CONFIG'][stated + modd])))
                except KeyError:
                    warnings.warn("state %s doesn't have config for module %d" % (name, modind),
                                  NoStateModuleConfigWarning)

            states[name] = modstates
        return states            
        
        
    @property
    @firsttime
    @getnumfromconfig('CONSTANTS')
    def constants(self,nconstants):            
        constants = {k:v for k,v in [defparse(line)for line in self._extractlines('CONSTANT',nconstants)]}
        return constants
        
    @property
    @firsttime
    @getnumfromconfig('PARAMETERS')
    def parameters(self,nparams):
        parameters = {k:v for k,v in [defparse(line) for line in self._extractlines('PARAMETER',nparams)]}
        #validate all parameters are integers, 20 bit max
        def validate_param(val):
            if val > 2**20 - 1:
                raise ValueError('invalid parameter value: larger than 20 bit')
            elif val < 0 :
                raise ValueError('invalid parameter value: less than 0')
            elif type(val) is not int:
                raise ValueError('invalid parameter: must be integer')
        map(validate_param, parameters.values())
                                      
        return parameters

if __name__ == '__main__':
    import os
    os.chdir('../seqs')
    fl = 'CCD250_20161109_LOW_GAIN-reversed-xed.acf'
    #fl = '../seqs/CCD250_20161109_LOW_GAIN-reversed-xed.acf'
    
    warnings.simplefilter('ignore',category=StateConfigWarning)
    
    archon_conf = acffile(fl)
    print(archon_conf.states)