#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 13:33:51 2017

@author: danw
"""

from collections import defaultdict
from functools import wraps
from enum import Enum

class archon_module_type(Enum):
    """ enum representing available archon module types"""
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


class ArchonInstructions(Enum):
    STATE = 0
    GOTO = 1
    CALL = 2
    DECREMENT = 3
    RETURN = 4
    CONDITIONAL =5
    REPEAT=6
 
    
ternaryrepr = {False : "_",
               True : "^",
               None : "-"}
    
class InvalidClockStateList(Exception):
    pass
    

class _ClockStateMeta(type):
    """metaclass which registers clock state types with the base class"""
    def __init__(cls,name,bases,nmspc):
        if hasattr(cls,"MODULE_TYPES"):
            for tp in cls.MODULE_TYPES:
                ClockState.MODULE_TYPE_LOOKUP[tp] = cls
        
        #wrap init to call superclass
        
        def initwrap(fun):
            @wraps(fun)
            def f(self,moduleinstance,statelist,*args,**kwargs):
                super(cls,self).__init__(moduleinstance,statelist)
                fun(self,*args,**kwargs)
            return f
            
        if cls.__name__ != 'ClockState':
            cls.__init__ = initwrap(cls.__init__)
            
    
class ClockState(metaclass=_ClockStateMeta):
    MODULE_TYPE_LOOKUP = {}
    MODULE_NAME = 'NONE'
    """ base class for archon clock state actions"""
    
    @classmethod
    def get_state_instance(cls,moduleinstance,statelist,*args,**kwargs):
        instance = ClockState.MODULE_TYPE_LOOKUP[moduleinstance.type](moduleinstance, statelist, *args,**kwargs)
        return instance
        
        
    def __init__(self,moduleinstance,statelist):
        self._moduleinstance = moduleinstance
        self._statelist = statelist
        
        
    def __repr__(self):
        return self.__class__.__name__  + str(self._statelist)
        
    def require_statelist_len(self,n):
        if len(self._statelist) != n:
            raise InvalidClockStateList(self.MODULE_NAME + ' object requires statelist of length: %d. Got length: %d' %(n,len(self._statelist)))
        
class ADState(ClockState):
    """class representing clock states applied to an AD module"""
    MODULE_TYPES = [archon_module_type.AD]
    MODULE_NAME = 'AD'    

    def __init__(self):
        #NOTE statelist magically filled in by metaclass
        self.require_statelist_len(2)
            
        self.clamp = self._statelist[0]
        self.flag = self._statelist[1]
            
    def __repr__(self):
        return 'ADState: CLAMP=%d, FLAG=%d' % (self.clamp,self.flag)


        
class BiasState(ClockState):
    """class representing clock states applied to bias modules"""
    MODULE_TYPES = [archon_module_type.LVBias,archon_module_type.LVXBias ,
                    archon_module_type.HVBias, archon_module_type.HVXBias]
    MODULE_NAME = 'BIAS'
    
    def __init__(self):
        #NOTE statelist magically filled in by metaclass
        self.validate_statelist()    
        
        if self.hasgpio:
            gpiovals = self._statelist[:16]
            
            #dictionary of (state,keep) tuple combinations
            #abuse of python None value for no change
            gpio_lookup = {(0,0) : False,
                           (0,1) : None,
                           (1,0) : True,
                           (1,1) : None}
            
            #lookup in pairs            
            self._setclocks = [gpio_lookup[_] for _ in zip(*[iter(gpiovals)]*2)]
    

    def __repr__(self):
            st = 'BiasState:'
            if self.hasgpio:
                gpiostr = "".join((ternaryrepr[_] for _ in self._setclocks))
                st += ' GPIO=[%s]' % gpiostr

            if self.cansetbias:
                biasstr = str(self._statelist[16:])
                st += 'BIASCMD=' + biasstr

            return st
            
                               
                
    def validate_statelist(self):
        if self._moduleinstance.version.build < 833:
            self.cansetbias = False
            
        if self._moduleinstance.type in [archon_module_type.LVBias, archon_module_type.LVXBias]:
            #only LV bias modules have GPIO
            self.hasgpio = True
        #see archon manual page 59 and 60
        if not self.hasgpio:
            #we're a high voltage state
            if not self.cansetbias:
#                TODO: NOT SPECIFIED, almost certainly 0
                self.require_statelist_len(0)
            else:    
                self.require_statelist_len(3)            
        else:
            #were a low voltage state
            if not self.cansetbias:
                self.require_statelist_len(16)
            else:
                self.require_statelist_len(19)
        
class SlewRate(Enum):
    SLOW = 0
    FAST = 1

class DriverState(ClockState):
    """class representing clock states applied to clock driver modules"""
    MODULE_TYPES = [archon_module_type.Driver]
    MODULE_NAME = 'DRIVER'
    def __init__(self):
        #NOTE statelist magically filled in by metaclass
        #list comes in groups of 3, and there are 8 channels
        self.require_statelist_len(24)
        
        vals = self._statelist[::3]        
        keep = self._statelist[2::3]
        
        self._slewrates = [SlewRate(_) for _ in self._statelist[1::3]]

        self._clockset = []
        for v,k in zip(vals,keep):
            if bool(k):
                self._clockset.append(None)
                continue
            self._clockset.append(v)

    def __repr__(self):
        syms = ['-'] * 8
        labels = {}
        i = 0
        for ind,(clock,slew) in enumerate(zip(self._clockset,self._slewrates)):
            if clock is None:
                continue
            if clock in labels:
                syms[ind] = labels[clock]
                if slew is SlewRate.SLOW:
                    syms[ind] +='*'

            else:
                labels[clock]=str(i)
                i+=1
        return 'CLOCKState: CHANGES=[' + ''.join(syms) + '], VALUES=[' + str(labels) + ']'
            
#TODO: implement HS, LVDS modules....