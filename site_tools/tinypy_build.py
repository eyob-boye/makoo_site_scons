#-------------------------------------------------------------------------------
# Copyright (C) 05/2017 Eyob Demissie
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
import os
import sys
import modulefinder
import level_tree
import operator
import shutil



def do_cmd(cmd):
    #print(cmd)
    r = os.system(cmd)
    if r:
        print(cmd)
        print('exit_status',r)
        sys.exit(r)

def sort_by_dependency(tp_modules):
    paths = []
    for mod in tp_modules:
        paths.append(os.path.dirname(mod))
    paths = sorted(list(set(paths)))

    tp_modules_with_main = []
    lt = level_tree.Tree()
    for mod in tp_modules:
        finder = modulefinder.ModuleFinder(path=paths)
        finder.run_script(mod)
        for name, m in finder.modules.iteritems():
            if name is "__main__":
                if "main" in m.globalnames.keys():
                    tp_modules_with_main.append(mod)
                continue
            if(m.__file__):
                lt.add_edge((mod, m.__file__))
            else:
                lt.add_edge((mod, name))
    lt.levelize()
    lt_levels_result = lt.get_level()
    #Sort the module by their dependency levels.
    lt_levels_result_sorted = sorted(lt_levels_result.iteritems(),
                                     key=operator.itemgetter(1))
    lt_levels_result_sorted = [(f[0], f[0] in tp_modules_with_main) for f in lt_levels_result_sorted]
    return lt_levels_result_sorted

def build_inits(tp_modules, outdir="."):
    """ Generate two files tp_app.c and t_app.h that contain the user module
    initializations. It is assumed that the module list is in order of low
    to higher dependencies. This is important since a module that imports another
    module will fail to initialize if the imported module has not been already
    initialized.
    """

    out_1 = ["""#include "tinypy.h" """,
             """static tp_vm *tp;"""]
    out_2 = ["""void TpApp_init()""",
             """{""",
             """    char *argv[] = {"", ""};""",
             """    tp = tp_init(1, argv);"""]
    out_3 = []
    out_4 = ["""void TpApp_mainFunction()""",
             """{"""]
    out_5 = ["""void TpApp_init(void);""",
             """void TpApp_mainFunction(void);"""]
    for m, has_main in tp_modules:
        m_name, m_ext = os.path.splitext(os.path.basename(m))
        if m_ext:
            out_1.append("""static void %s_init(TP)""" % m_name)
            out_1.append("""{""")
            out_1.append("""    extern const unsigned char tp_%s[];""" % m_name)
            out_1.append("""    extern unsigned long tp_%s_sizeof;""" % m_name)
            out_1.append("""    tp_import(tp,0,"%s",(void *)tp_%s, tp_%s_sizeof);"""%(m_name,m_name,m_name))
            out_1.append("""}""")
        else:
            if m_name is not "sys":
                out_1.append("""extern void %s_init(TP);"""%m_name)
        if m_name is not "sys":
            out_2.append("""    %s_init(tp);"""%m_name)
        if has_main:
            out_3.append("""void TpApp_mainFunction__%s() { tp_ez_call(tp,"%s","main",tp_None); }""" % (m_name, m_name))
            out_4.append("""    tp_ez_call(tp,"%s","main",tp_None);""" % m_name)
            out_5.append("""void TpApp_mainFunction__%s(void);""" % m_name)
    out_2.append("""}""")
    out_4.append("""}""")
    out_1.append("")
    out_2.append("")
    out_3.append("")
    out_4.append("")
    f = open(os.path.join(outdir,'tp_app.c'),'w')
    f.write('\n'.join(out_1+out_2+out_3+out_4))
    f.close()

    out_5 = ["""#ifndef TP_APP_H""",
             """#define TP_APP_H""", "",
             """#ifdef __cplusplus""",
             """extern "C" {""",
             """#endif""",""] + out_5
    out_5+= ["",
             """#ifdef __cplusplus""",
             """}""",
             """#endif""","",
             """#endif"""]
    f = open(os.path.join(outdir,'tp_app.h'),'w')
    f.write('\n'.join(out_5))
    f.close()

def build_bc(tp_modules=[], tinypy_path=".", outdir="."):
    out = []
    for m, has_main in tp_modules:
        m_name, m_ext = os.path.splitext(os.path.basename(m))
        m_out = os.path.abspath(os.path.join(outdir, "%s.tpc" % m_name))
        py2bc_cmd = os.path.abspath(os.path.join(tinypy_path, "tinypy/py2bc.py"))
        # TODO: Expose -nopos option to the upper builder so that user can build either way
        #-nopos option strips out the python source location information when
        # exception happens during runtime.
        #do_cmd('python %s %s %s'%(py2bc_cmd, m, m_out))
        do_cmd('"%s" %s %s %s -nopos'%(sys.executable, py2bc_cmd, m, m_out))
        out.append("""const unsigned char tp_%s[] = {""" % m_name)
        data = open(m_out,'rb').read()
        cols = 16
        for n in xrange(0,len(data),cols):
            out.append(",".join([str(ord(v)) for v in data[n:n+cols]])+',')
        out.append("""};""")
        out.append("""unsigned long tp_%s_sizeof = sizeof(tp_%s);""" % (m_name, m_name))
    out.append("")
    f = open(os.path.join(outdir,'tp_app_bc.c'),'w')
    f.write('\n'.join(out))
    f.close()

def path_to_posix(path):
    os.path.abspath(path)
    path_posix = path.replace(":", "").replace("\\", "/")
    if path_posix[0] != "/":
        path_posix = "/" + path_posix
    return path_posix

def build_blob(tp_internal_modules=[], tinypy_path=".", outdir="."):
    """ This function generates the tinypy system files as one big file (i.e blob)
    """
    do_cmd('"%s" %s blob %s > %s' % (sys.executable, os.path.join(tinypy_path, "setup.py"), " ".join(tp_internal_modules), os.devnull))
    src_root = os.path.join(tinypy_path,"build")
    for f in ["tinypy.c", "tinypy.h", "tinypy_libs.c"]:
        shutil.copy(os.path.join(src_root, f), os.path.join(outdir, f))

    out_1 = ["""#""",
             """# Component make file""",
             """#""",
             """""",
             """COMPONENT_SRCDIRS := .""",
             """""",
    ]
    priv_includes = []
    for m in tp_internal_modules:
        priv_include = os.path.relpath(os.path.join(tinypy_path,"modules", m), os.path.abspath(outdir))
        priv_includes.append(path_to_posix(priv_include))
    out_1.append("""COMPONENT_PRIV_INCLUDEDIRS := . %s""" % " ".join(priv_includes))
    out_1.append("""""")
    out_1.append("""COMPONENT_ADD_INCLUDEDIRS := .""")
    out_1.append("""""")
    with open(os.path.join(outdir, "component.mk"), "w") as ofile:
        ofile.write("\n".join(out_1))

def build_app(tp_modules=[], tinypy_path=".", outdir="."):
    """ This function generates the byte codes for tinypy modules and also generates
    c code to initialize them.
    """
    tp_modules_abs = []
    for m in tp_modules:
        tp_modules_abs.append(os.path.abspath(m))
    tp_modules_abs_sorted = sort_by_dependency(tp_modules_abs)

    # Only the user modules we generate the byte code.
    tp_modules_abs_sorted_useronly = []
    for mod in tp_modules_abs_sorted:
        if mod[0] in tp_modules_abs:
            tp_modules_abs_sorted_useronly.append(mod)

    build_bc(tp_modules_abs_sorted_useronly, tinypy_path, outdir)
    build_inits(tp_modules_abs_sorted, outdir)


#if __name__ == '__main__':
#    MY_MODULES = ["test1.py", "test2.py", "test3.py"]
#    build(MY_MODULES, "C:/dev/tinypy", ".")