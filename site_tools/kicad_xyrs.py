#-------------------------------------------------------------------------------
# Copyright (C) 09/2016 Eyob Demissie
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
"""

Tool-specific initialization for kicad_xyrs.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""
__revision__ = ""

import os.path
import sys

import SCons.Action
import SCons.Builder
import SCons.Util


def find(env, key_program):
    # First search in the SCons path and then the OS path:
    pcbnew_com = (env.WhereIs(key_program) or SCons.Util.WhereIs(key_program))
    
    # If we cannot find it, then try to calculate from an environment
    # variable that is usually added when kicad installs.
    if not pcbnew_com:
        kisysmod = os.environ['KISYSMOD']
        
        if kisysmod:
            kisysmod_parts = os.path.normpath(kisysmod).split(os.path.sep)
            pcbnew_com = []
            for i,p in enumerate(kisysmod_parts):
                if i == 0 and p == "":
                    p = "/"  #unix root
                if p == "share":
                    break
                pcbnew_com.append(p)
            #FIXME: make glob search for the file to make it os neutral
            pcbnew_com += ["bin", "pcbnew.exe"]  
            pcbnew_com = "/".join(pcbnew_com)
    return pcbnew_com


def kicadxyrs_Emitter(target, source, env):
    # Expecting the kicad_pcb file in source[0]
    # We use it to add .net file as one of the sources
    # for the .xyrs target.
    adjustixes = SCons.Util.adjustixes
    bs = SCons.Util.splitext(str(source[0].name))[0]
    bs = os.path.join(str(source[0].get_dir()),bs)
    source.append(adjustixes(bs,'', '.net'))
    return target, source


def generate(env):
    """Add a Builder factory function and construction variables for
    kicad xyrs builder to an Environment."""
    if not env.has_key('KICAD_PYTHONCOM'):
        pcbnew_com = find(env, 'pcbnew')
        if pcbnew_com:
            pcbnew_com_dir = os.path.dirname(pcbnew_com)
        else:
            print("Error: While loading Kicad Gerber scons tool, cannot find pcbnew executable.")
            print("Please add executable path on the path variable.")
            env.Exit(1)
        env['KICAD_PYTHONCOM']  = os.path.join(pcbnew_com_dir, "python.exe")

    Builder = SCons.Builder.Builder

    def builder_print_action():
        # Suppress action command line printing... each action has its own
        # pretty message.
        pass

    env['__kicad_gen_xyrs_py'] = os.path.join(env.Dir('#site_scons/site_tools').abspath, "gen_xyrs.py")
    first_action = SCons.Action.Action( '$KICAD_PYTHONCOM  "$__kicad_gen_xyrs_py" -i ${SOURCE.srcdir.abspath}/${SOURCE.name}  -o ${TARGET}',
              'Generating:  XYRS file for "$SOURCE.name"'
              ,
              show=builder_print_action)

    kicad_xyrs_builder_action = [first_action]
    kicad_xyrs_builder = Builder(action = kicad_xyrs_builder_action,
                                 emitter = kicadxyrs_Emitter)

    env.Append(BUILDERS = {'KiCadXYRS' : kicad_xyrs_builder})

def exists(env):
    return find(env)
