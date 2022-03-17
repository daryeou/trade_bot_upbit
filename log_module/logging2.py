# -*- coding: utf-8 -*-
from colorama import Fore, Back, Style
from functools import wraps
from datetime import datetime
#from weakref import WeakValueDictionary
import atexit
import os

'''
Please write on main.py:
----------------------------------
    DEBUG_MODE=True
    if DEBUG_MODE:
        debug_on()
    else:
        logit = no_logit
        debug, debug_str, debug_repr = no_debug
----------------------------------

Usage:
----------------------------------
    Decorator(save log file):   @logit
    Create Class                log = Log(1) if parameter is 1: run 
                                                            0:not run
    Remove Class                del log
    print debug log: 
                                log.debug(text)
                                log.debug_repr(object)
                                log.debug_str(object)
                                
                                log.no_debug(text)
                                
                                
----------------------------------
'''

class Singleton(type):
    #_instance = WeakValueDictionary()
    _instance = {}
    def __call__(cls,*args,**kwargs):
        print("-------singleton created--------")
        if cls not in cls._instance:
            cls._instance[cls] = super(Singleton,cls).__call__(*args,**kwargs)
        return cls._instance[cls]
    

log_file=None
#log_file = open(os.path.join(os.path.abspath('debug') , f'{datetime.now():%Y.%m.%d}.log'),"w+")
debug_mode=False

def log_init():
    global log_file
    log_file = open(f'./debug {datetime.now():%Y.%m.%d_%I.%M.%S}.log',"w+")


'''
save Log file
TODO: 멀티프로세서로 만들어서 렉 줄일 것
'''
def logit(func):
    global log_file
    @wraps(func)
    def with_logging(*args, **kwargs):
        log_file.write(f'{datetime.now():%Y.%m.%d %I:%M:%S.%f} >> {func.__name__} >> {args}\n')
        log_file.flush()
        #if hasattr(func, "__call__"): #func가 함수일 경우 실행
        return func(*args, **kwargs)
    return with_logging

class Log(metaclass = Singleton):
    '''
    Debug mode
    print Log
    '''
    @staticmethod
    @logit
    def debug_(text="None Log"):
        print(Back.GREEN + f'{datetime.now():%Y.%m.%d/%I:%M:%S.%f} >> {Style.RESET_ALL} {text}') #print(f'{datetime.now():%Y-%m-%d %p %H:%M:%S.%f}: {text}')
        print(Style.RESET_ALL)
            
    '''
    Debug mode
    print repr Log
    '''
    @staticmethod
    @logit
    def debug_repr_(text="None Log"):
        print(f'{datetime.now():%Y.%m.%d/%I:%M:%S.%f} >> {text!r}') #print(f'{datetime.now():%Y-%m-%d %p %H:%M:%S.%f}: {text!r}')
        print(Style.RESET_ALL)
            
    '''
    Debug mode
    print str Log
    '''
    @staticmethod
    @logit
    def debug_str_(text="None Log"):
        print(f'{datetime.now():%Y.%m.%d/%I:%M:%S.%f} >> {text!s}') #print(f'{datetime.now():%Y-%m-%d %p %H:%M:%S.%f}: {text!s}')
        print(Style.RESET_ALL)
        
    @staticmethod
    def no_debug(text):
        pass
    
    '''
    print Error
    '''
    @staticmethod
    class expError():
        def __init__(self,Exception):
            self.Exception = Exception
            self.debug("Error : " + str(self.Exception))
        def __str__(self):
            return str(self.Exception)
        def __enter__(self):
            pass
        def __exit__(self, type, value, trace_back):
            return True;
    
    def __init__(self,mode=1):
        global debug_mode
        if mode==1:
            debug_mode=True
            self.debug = self.debug_
            self.debug_repr = self.debug_repr_
            self.debug_str = self.debug_str_
            self.debug("DEBUG_ON" if debug_mode == True else "DEBUG_OFF")
            self.debug(f'START : {datetime.now()!r}')
        else:
            debug_mode=False
            self.debug = self.no_debug
            self.debug_repr = self.no_debug
            self.debug_str = self.no_debug
        
    def clear(self):
        global debug_mode
        debug_mode = False
        self.debug(f'END : {datetime.now()!r}')
        global log_file
        log_file.flush()
        log_file.close()
        print("file closed :" , f'{log_file.closed}')
            




        