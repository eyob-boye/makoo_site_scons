#-------------------------------------------------------------------------------
# Copyright (C) 04/2017 Eyob Demissie
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THETHE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Except as contained in this notice, the name(s) of the above copyright holders 
# shall not be used in advertising or otherwise to promote the sale, use or other
# dealings in this Software without prior written authorization.
#-------------------------------------------------------------------------------
import SCons.Environment
import os, sys

# This class is used to track the dependencies among component
# scripts. Since it is usually one script to one component, it implies that
# circular reference is a circular dependency in the components themselves.
# This might seem trivial but it is invaluable as the component count grows.
class ComponentDepTree:
    def __init__(self, silent=False):
        self.silent = silent
        self.nest_level = -1
        self.entered_scripts = []
        self.log = ""
        self.indent="   "
        self.env = SCons.Environment.Environment(tools = ['empty'])

    def reset_level(self):
        self.nest_level = 0
        self.entered_scripts = []
        self.log = ""

    def get_script_dir(self, sd):
        return self.env.Dir('#').rel_path(self.env.Dir(sd).srcnode())

    def get_msg_indent(self):
        """This function returns the current indent size. Can be used by
        external entities to align their message printing."""
        return self.indent * self.nest_level

    def script_enter(self, script_dir='.', msg_postfix=''):
        sd = self.get_script_dir(script_dir)
        self.nest_level += 1

        if self.nest_level == 0:
            print(75*'-')

        if sd in self.entered_scripts:
            msg = self.indent*self.nest_level + "Reading again [%s]" % sd
            self.log += (os.linesep + msg)
            if not self.silent:
                print(msg)
            else:
                self.log += (os.linesep + msg)
            print("Framework error: A circular reference in the components.")
            print("One of the dependencies of [%s] is circling back and ")
            print("and calling it again. Otherwise, make sure that all")
            print("script_enter() and script_exit() functions are being")
            print("called in pairs.")
            print(75*'-')
            sys.exit(1)
        #elif(is another version of same component imported already) <-- TODO
        else:
            self.entered_scripts.append(sd)
            msg = self.indent*self.nest_level + "Reading [%s]%s" % (sd, msg_postfix)
            self.log += (os.linesep + msg)
            if not self.silent:
                print(msg)
            else:
                self.log += (os.linesep + msg)
                print(self.log)

    def script_exit(self, script_dir='.', msg_postfix=''):
        sd = self.get_script_dir(script_dir)
        if not sd in self.entered_scripts:
            msg = self.indent*self.nest_level + "Exiting [%s]%s" % (sd, msg_postfix)
            self.log += (os.linesep + msg)
            if not self.silent:
                print(msg)
            else:
                self.log += (os.linesep + msg)
                print self.log
            print("Framework error: Trying to exit script that we did not enter.")
            print("This is due to unbalanced enter/exit calls in the script.")
            print("Make sure that all script_enter() and script_exit()")
            print("functions are being called in pairs.")
            print(75*'-')
            sys.exit(1)
        else:
            msg = self.indent*self.nest_level + "Exiting [%s]%s" % (sd, msg_postfix)
            self.log += (os.linesep + msg)
            if not self.silent:
                print(msg)
            else:
                self.log += (os.linesep + msg)

        if self.nest_level == 0:
            print(75*'-')

        self.nest_level -= 1
        self.entered_scripts.remove(sd)

def CreateDepTree(silent=False):
    return ComponentDepTree(silent)
