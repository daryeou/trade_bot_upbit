# -*- coding: utf-8 -*-

'''
from contextlib import contextmanager

@contextmanager
def open_file(name):
    f = open(name, 'wb')
    yield f
    f.close()
'''

'''
Usage 1-->
        with File("test.log",'w+') as open_file:
            open_file.write(f'test\n')
Usage 2-->
        file = File("log.txt","w+")()
            file.write(f'test\n')
'''
class File(object):
    def __init__(self, file_name, method):
        self.file_obj = open(file_name, method)
    def __call__(self):
        return self.file_obj
    def __enter__(self):
        return self.file_obj
    def __exit__(self, type, value, trace_back):
        if type != None:
            print("file open failed",type,value)
            return False
        self.file_obj.close()
        return True
