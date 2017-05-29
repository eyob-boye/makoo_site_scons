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
import SCons.Environment
import os
import glob
import fnmatch


def _GetComponentFromGit(env, target, source):
    """This function is used to import a single component from git repository.
       The SourceCode() builder can be used for this but there is a problem.
       The components have SConscript files that need to be read during the
       reading phase of the SCons. If the SourceCode() target is not built, there
       is no way find the SConscript. So we are forced to use this function
       which gets the components immediately during the reading phase of the
       SConstcripts.
    

       For github there is a possbility of using svn export itself... since
       they have svn interface to the git repos but for now we use git
       itself directly.
       We have two choices git archive or git clone
       Since the archive is not supported in github then we don't use it,
       although bitbucket allows it (not verified this).
       
       So we clone and delete .git file. For now, I am not deleting .git
       I need to figure out if this is a good idea or not.
       
       git_ret = gc_env.Execute('git clone --depth=1 "%s" "%s"' % (source, trgt))
       if git_ret != 0:
           There is an error
       else:
           Remove the .git folder in the newly cloned location to make it
           plain vanilla code.
    """
    gc_env = env.Clone()
    trgt = gc_env.Dir(target).srcnode().abspath
    def gc_print_cmd_line(s, target, source, env):
        # do not print the command line.
        pass
    def gc_show_cmd(env, trgt):
        print("*** Importing component - [%s] ***" % \
                                 env.Dir('#').rel_path(env.Dir(trgt).srcnode()))
    gc_env['PRINT_CMD_LINE_FUNC'] = gc_print_cmd_line
    if not os.path.exists(trgt):
        trgt_unix_like_path = env.Dir(trgt).srcnode().abspath
        trgt_unix_like_path = trgt_unix_like_path.replace('\\', '/')
        print "nix ",source, trgt_unix_like_path
        git_ret = gc_env.Execute('git clone --depth=1 --recursive -q -c advice.detachedHead=false %s "%s"' % (source, trgt_unix_like_path),
                                  show=gc_show_cmd(gc_env, trgt))
        if git_ret!=0:
            print("-"*75)
            print("Build Script Error: Problem trying to import component.")
            print("Make sure you have typed component name, version correctly.")
            print("In addition, it may be a network connection problem.")
            print("Try again.")
            print("-"*75)
            gc_env.Exit(1)

        #Clean up
        #git_repo = os.path.join(trgt, ".git")
        #if (os.path.exists(git_repo)):
        #    # Remove it.


def _glob_recursive(search_path, patterns, exclude_path=[]):
    matches = []
    for root, dirnames, filenames in os.walk(search_path):
        if [e for e in exclude_path if e in root]:
            continue
        for p in patterns:
            for filename in fnmatch.filter(filenames, p):
                matches.append(os.path.join(root, filename))
            for dirname in fnmatch.filter(dirnames, p):
                matches.append(os.path.join(root, dirname))
    return matches


def _FindComponentFiles(env, suffix=[], exclude=[], search_root=None, recursive=False):
    """ This function is used to find the component's files by looking at the
    the present source directory."""
    suffix = env.Flatten(suffix)
    exclude = env.Flatten(exclude)

    if search_root is None:
        # Search under the present source directory.
        search_root = os.path.join(env.Dir('#').abspath,
                                   env.Dir('.').srcnode().path)
        search_path = search_root
    else:
        search_path = search_root

    m_f=[]
    if recursive:
        m_f = _glob_recursive(search_path, ["*."+ext for ext in suffix], [".git", ".svn", ".bzr", ".hg"])
    else:
        for ext in suffix:
            for a in sorted(set([''])):
                search_path = os.path.join(search_path,a)
                m_f += env.Flatten(glob.glob(os.path.join(search_path,'*.'+ext)))

    m_f_filtered = []
    for f in m_f:
        # Check each file name and if it contains
        # "unittest" exclude from the list.
        # Filter the files and folders in the exclude list.
        if os.path.isdir(f):
            m_f_filtered.append(env.Dir(f))
        else:
            fparts = f.replace("\\", "|||").replace("/", "|||").split("|||")
            fb = os.path.basename(f)
            if ('unittest' not in fb.lower()):
                if not [e for e in exclude if e in fparts]:
                    m_f_filtered.append(env.File(f))
    return m_f_filtered


def _MergeDicts(env, d1, d2):
    """This function merges dictionary d2 into d1. This is a very useful
    operation that we need repeatedly as we do recursive calls into
    component sconscripts. So it is added as part of the env so all the
    scripts have access to it without importing anything. For each key, the
    value is merged into a flattened list. Then it is sorted. If the items
    items are scons File() nodes their path is used to sort, otherwise
    they are just sorted as normal python objects."""
    if not d2: d2={}
    if not d1: d1={}
    for k in d2:
        if k in d1:
            d=set(env.Flatten(list((d1[k] + d2[k],))))
            try:
                d=sorted(d, cmp=lambda x,y: cmp(x.path, y.path))
            except AttributeError:
                d=list(sorted(d))
            d1[k] = d
        else:
            d1[k]=d2[k]


def _ExtendEnvironment(envclass):
    envclass.GetComponentFromGit = _GetComponentFromGit
    envclass.FindComponentFiles = _FindComponentFiles
    envclass.MergeDicts = _MergeDicts
_ExtendEnvironment(SCons.Environment.Environment)


import SCons.Script
__site_init_file = os.path.abspath(__file__)
def _MakooSiteSconsGetPath(item):
    """ Given an item name, this function gets the absolute
    path of the item, within the site_scons or site_tools
    subfolder. This function exists to make sure that
    scripts that reference items in this folder do not have
    to be worried where site_scons folder is placed.
    """
    site_scons_path = os.path.dirname(__site_init_file)
    if not item:
        return site_scons_path
    else:
        item_abs = os.path.join(site_scons_path, item)
        if os.path.isfile(item_abs):
            return item_abs
        item_abs = os.path.join(site_scons_path, "site_tools", item)
        if os.path.isfile(item_abs):
            return item_abs
        print("Error: Cannot find [%s] in [%s]." % (item,site_scons_path))
        return None

SCons.Script.MakooSiteSconsGetPath = _MakooSiteSconsGetPath



