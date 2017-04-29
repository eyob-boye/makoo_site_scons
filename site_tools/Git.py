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

Tool-specific initialization for Git.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""
__revision__ = ""

import os.path
import string

import SCons.Action
import SCons.Builder
import SCons.Util

def find(env, key_program):
    # First search in the SCons path and then the OS path:
    return env.WhereIs(key_program) or SCons.Util.WhereIs(key_program)

def generate(env):
    """Add a Builder factory function and construction variables for
    Git to an Environment."""
    git_com = find(env, 'git')
    if git_com:
        git_com_dir = os.path.dirname(git_com)
        #FIXME: Do a sanity check... on Windows git_base_folder/cmd is the
        #appropriate path instead of git_base_folder/bin path

        # The git command directory must be added to the path:
        path = env['ENV'].get('PATH', [])
        if not path:
            path = []
        if SCons.Util.is_String(path):
            path = string.split(path, os.pathsep)
            
        env['ENV']['PATH'] = string.join([git_com_dir] + path, os.pathsep)

    else:
        print("Error: While loading Git scons tool cannot find git executable.")
        print("Please add executable path on the path variable.")
        env.Exit(1)

    def GitFactory(repos, module='', env=env):
        """ """
        # fail if repos is not an absolute path name?
        if module != '':
            module = module + '/'
        act = SCons.Action.Action('$GITCOM', '$GITCOMSTR')
        return SCons.Builder.Builder(action = act,
                                     env = env,
                                     GITREPOSITORY = repos,
                                     GITMODULE = module)

    env.Git = GitFactory

    env['GIT']      = 'git'
    env['GITFLAGS'] = SCons.Util.CLVar('')
    env['GITCOM']   = '$GIT clone --depth=1 $GITFLAGS $GITREPOSITORY ${TARGET.srcdir.abspath}/${TARGET.name}'

def exists(env):
    return env.Detect('git')
