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
import os.path
import SCons.Tool
import SCons.Util
from xml.etree import ElementTree as ET

def kicadprj_Emitter(target, source, env):
    adjustixes = SCons.Util.adjustixes
    bs = SCons.Util.splitext(str(target[0].name))[0]
    bs = os.path.join(str(target[0].get_dir()),bs)
    # first target (.pro) is automatically added by builder
    if len(target) < 2:
        # second target is the actual .sch file.
        target.append(adjustixes(bs,'', '.sch'))
    if len(target) < 3:
        # third target is footprint lib table specific to the kicad project.
        target.append("fp-lib-table")
    return target, source


def sort_libs_and_pretties(target, source, env):
    # Iterate through each source to sort into lib and pretty nodes
    prj_dir = target[0].get_dir()
    PrjDir = env.Dir(prj_dir)
    
    prj_sources=SCons.Util.flatten(list((source,)))
    prj_items={'.lib':[], '.pretty':[]}
    for s in prj_sources:
        if type(s)==type(''): f=env.File(s)
        s_ext = os.path.splitext(s.name)[1].lower()
        if prj_items.has_key(s_ext):
            prj_items[s_ext].append(s)
        else:
            #ignore unknown file type
            pass
    return prj_items


def kicad_project_builder(target, source, env):
    fs = target[0]
    
    if os.path.isfile(fs.abspath):
        # If .pro file exists, then open it and reconstruct the LibDir= line
        # and the LibName*=* lines preserving everything else.
        with open(fs.abspath, 'r') as ifile:
            pro_file_cont_lines = []
            LibDir_lines = []
            LibName_lines = []
            for line in ifile.readlines():
                if "LibDir=" in line:
                    LibDir_lines.append(line)
                    if len(LibDir_lines) == 1:
                        line = "LibDir=%s\n"
                    else:
                        line = None
                elif "LibName" in line:
                    LibName_lines.append(line)
                    if len(LibName_lines) == 1:
                        line = "%s\n"
                    else:
                        line = None
                if line is not None:
                    pro_file_cont_lines.append(line)
            pro_file_cont = "".join(pro_file_cont_lines)
            if pro_file_cont.count("%s") != 2:
                print("Error: Could not find the LibDir or LibName lines in %s" % target[0].name)
                env.Exit(1)
    else:
        # There is no existing project file, read in a template and modify it.
        prj_template = env.Dir('#site_scons/site_tools').abspath
        prj_template = os.path.join(prj_template, 'kicad_project_template.pro')
        if not  os.path.isfile(prj_template):
            print("Unexpected error. Cannot find the project template")
            print("site_scons/site_tools/kicad_project_template.pro")
            env.Exit(1)
        with open("./site_scons/site_tools/kicad_project_template.pro", 'r') as ifile:
            pro_file_cont = "".join(ifile.readlines())

    prj_items = sort_libs_and_pretties(target, source, env)

    libs = []
    for r in prj_items['.lib']:
        path = env.Dir('.').rel_path(r.srcnode())
        basename = os.path.splitext(os.path.basename(path))[0]
        libs.append((basename, os.path.split(path)[0].replace("\\", "/")))

    # Prepare the library lists for *.pro and *.sch files
    lib_dir = []
    lib_list_1 = []
    for i,(libn, libpath) in enumerate(libs,1):
        libpath = "${KIPRJMOD}/%s"%libpath
        if libpath not in lib_dir:
            lib_dir.append(libpath)
        lib_list_1.append("LibName%s=%s" % (i,libn))
    if not lib_list_1:
        lib_list_1.append("LibName=")

    pro_file_cont = pro_file_cont % (";".join(lib_dir), "\n".join(lib_list_1))
    with open(fs.abspath, "w") as ofile:
        ofile.write(pro_file_cont)


def kicad_schematic_builder(target, source, env):
    fs = target[1]

    if os.path.isfile(fs.abspath):
        # If .sch file exists, then open it and reconstruct the LIB: lines
        # preserving everything else.
        with open(fs.abspath, 'r') as ifile:
            sch_file_cont_lines = []
            LIBS_lines = []
            for line in ifile.readlines():
                if "LIBS:" in line:
                    LIBS_lines.append(line)
                    if len(LIBS_lines) == 1:
                        line = "%s\n"
                    else:
                        line = None
                if line is not None:
                    sch_file_cont_lines.append(line)
            sch_file_cont = "".join(sch_file_cont_lines)
            if sch_file_cont.count("%s") != 1:
                print("Error: Could not find the LIBS: lines in %s" % target[0].name)
                env.Exit(1)
    else:
        # There is no existing schematic file, read in a template and modify it.
        sch_template = env.Dir('#site_scons/site_tools').abspath
        sch_template = os.path.join(sch_template, 'kicad_project_template.sch')
        if not  os.path.isfile(sch_template):
            print("Unexpected error. Cannot find the project template")
            print("site_scons/site_tools/kicad_project_template.sch")
            env.Exit(1)
        with open("./site_scons/site_tools/kicad_project_template.sch", 'r') as ifile:
            sch_file_cont = "".join(ifile.readlines())

    prj_items = sort_libs_and_pretties(target, source, env)

    libs = []
    for r in prj_items['.lib']:
        path = env.Dir('.').rel_path(r.srcnode())
        basename = os.path.splitext(os.path.basename(path))[0]
        libs.append((basename, os.path.split(path)[0].replace("\\", "/")))

    # Prepare the library lists for *.pro and *.sch files
    lib_dir = []
    lib_list_2 = []
    for i,(libn, libpath) in enumerate(libs,1):
        libpath = "${KIPRJMOD}/%s"%libpath
        if libpath not in lib_dir:
            lib_dir.append(libpath)
        lib_list_2.append("LIBS:%s" % libn)
    prj_name = os.path.splitext(os.path.basename(fs.abspath))[0]
    lib_list_2.append("LIBS:%s-cache"%prj_name)

    sch_file_cont = sch_file_cont % "\n".join(lib_list_2)
    with open(fs.abspath, "w") as ofile:
        ofile.write(sch_file_cont)


def kicad_fplibtable_builder(target, source, env):
    fs = target[2]

    prj_items = sort_libs_and_pretties(target, source, env)
    
    fp_lib_table = ""
    fp_lib_table += "(fp_lib_table\n"
    for r in prj_items['.pretty']:
        path = env.Dir('.').rel_path(r.srcnode())
        basename = os.path.splitext(os.path.basename(path))[0]
        fp_lib_table += '  (lib (name %s)(type KiCad)(uri %s)(options "")(descr ""))\n' % (basename, "${KIPRJMOD}\%s"%path)
    fp_lib_table += ")\n"

    with open(fs.abspath, "w") as ofile:
        ofile.write(fp_lib_table)


def find(env):
    return not None


def generate(env):
    """Add builders and construction variables for KiCad project builder to the Environment."""
    Builder = SCons.Builder.Builder

    def builder_print_action():
        # Suppress action command line printing... each action has its own
        # pretty message.
        pass

    def adj_ext_for_msg(target, new_ext):
        fname = os.path.splitext(target)
        return fname[0]+new_ext

    env['__kicadprj_adjext'] = adj_ext_for_msg

    # A multi stage builder that,
    #    - generate .pro file
    #    - generate .sch file
    #    - generate fp-lib-table file
    first_action = SCons.Action.Action(kicad_project_builder,
              'Generating: "$TARGET.name" (Kicad project file)',
               show=builder_print_action)
    second_action = SCons.Action.Action(kicad_schematic_builder,
              'Generating: "${__kicadprj_adjext(TARGET.name,".sch")}" (Schematic file for project)',
               show=builder_print_action())
    third_action  = SCons.Action.Action(kicad_fplibtable_builder,
              'Generating: "fp-lib-table" (Foot print table for the project)',
               show=builder_print_action)
               
    kicad_prj_builder_action = [first_action, second_action, third_action]
    kicad_prj_builder = Builder (action = kicad_prj_builder_action,
                                 emitter = kicadprj_Emitter,
                                 suffix='.pro')

    env.Append(BUILDERS = {'KiCadProject' : kicad_prj_builder})


def exists(env):
    return find(env)
