import os.path
import SCons.Tool
import SCons.Util
from xml.etree import ElementTree as ET

def indent(elem, level=0):
    """ This function is used to indent the xml tree. It modifies the the
    passed in element.
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def cb_project_builder(target, source, env):
    """ This function constructs code::blocks project xml file for a console
    program that is going to be compiled with gcc.
    The source input is expected to be a list containing the following nodes.
    [ list of .c file nodes,
      list of .s files - assembly file nodes,
      list of .h source file nodes,
      linker command files,
      include dirs
    ]
    """
    cb_prj_name = os.path.splitext(target[0].name)[0]
    cb_prj_dir = target[0].get_dir()
    CBPrjDir = env.Dir(cb_prj_dir)

    # Iterate through each source to find the relative paths. The relative
    # path is with respect to the code:blocks project file.
    prj_sources=SCons.Util.flatten(list((source,)))
    prj_items={'.c':[], '.s':[], '.h':[], 'include_dirs':[]}
    for s in prj_sources:
        if type(s)==type(''): f=env.File(s)
        s_ext = os.path.splitext(s.name)[1].lower()
        if prj_items.has_key(s_ext):
            s_rel = CBPrjDir.rel_path(s.srcnode())
            prj_items[s_ext].append(s_rel)
            if s_ext=='.h':
                prj_items['include_dirs'].append(os.path.dirname(s_rel))
        else:
            #ignore unknown file type
            pass

    # Reconcile with the include directory from the environment preprocessor
    # path var. just in case it refers to additional .h files that are not
    # included as part of the project items. Such as the compiler.h for example.
    if env.has_key('CPPPATH'):
        for p in list(set(SCons.Util.flatten(env['CPPPATH']))):
            if type(p)==type(''): p=env.Dir(p)
            prj_items['include_dirs'].append(CBPrjDir.rel_path(p.srcnode()))
    # Get rid of duplicates and sort.
    prj_items['include_dirs']=sorted(set(prj_items['include_dirs']))

    # Read in the code::blocks project template file into an xml tree.
    # Then the tree is modified according to the project source files.
    xml_template = env.Dir('#site_scons/site_tools').abspath
    xml_template = os.path.join(xml_template, 'codeblocks_ide_prj_gcc_template.xml')
    if not xml_template:
        print("Unexpected error. Cannot find the code::blocks project template")
        print("site_scons/site_tools/codeblocks_ide_prj_gcc_template.xml")
        env.Exit(1)

    try:
        tree = ET.parse(xml_template)
    except Exception, inst:
        print("\nUnexpected error opening %s: %s" % (xml_template, inst))
        env.Exit(1)

    compiler_element = tree.find('Project/Compiler')
    for d in prj_items['include_dirs']:
        add_element = ET.Element("Add", directory=d)
        compiler_element.append(add_element)

    project_element = tree.find('Project')

    # Replace the template's default project title
    for e in project_element.findall('Option'):
        if e.get('title'):
            e.set('title', cb_prj_name)

    # Replace the template's target output name
    for t in project_element.findall('Build/Target'):
        for e in t.findall('Option'):
            out = e.get('output')
            if out:
                out = os.path.join(os.path.split(out)[0], cb_prj_name)
                e.set('output', out)

    no_opt_srcs = prj_items['.h']
    for s in no_opt_srcs:
        unit_element = ET.Element("Unit", filename=s)
        project_element.insert(5, unit_element)

    opt_srcs = prj_items['.c'] + prj_items['.c']
    option_element = ET.Element("Option", compilerVar="CC")
    for s in opt_srcs:
        unit_element = ET.Element("Unit", filename=s)
        unit_element.append(option_element)
        project_element.insert(5, unit_element)

    indent(tree.getroot())

    xml_o_file = target[0].srcnode().abspath
    try:
        xml_o_file = open(xml_o_file, 'w')
    except Exception, inst:
        print("\nUnexpected error opening %s: \n%s" % (xml_o_file, inst))
        env.Exit(1)

    xml_o_file.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
    xml_o_file.write(ET.tostring(tree.getroot()))
    xml_o_file.write('\n')
    xml_o_file.close()


def find(env, key_program):
    # First search in the SCons path and then the OS path:
    return env.WhereIs(key_program) or SCons.Util.WhereIs(key_program)


def generate(env):
    #Add a builder for building the Code::Blocks project file.
    cb_prj_com = SCons.Action.Action(cb_project_builder, '$CBPRJCOMSTR')
    cb_prj_blder = SCons.Builder.Builder(action = cb_prj_com,
                                         suffix = '.cbp')
    env.Append(BUILDERS = {'IDEProject' : cb_prj_blder})

    env['IDENAME'] = 'codeblocks'
    env['CBPRJCOMSTR'] = 'Generating Code::Blocks project file \n $TARGET \n'


def exists(env):
    return find(env)
