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
from optparse import OptionParser
import os, sys
try:
    import pcbnew as PN
except:
    print("This script needs to be executed by using")
    print("python.exe distributed by kicad. You can")
    print("find it in kicad/bin folder.")


def isModuleSMD(module):
    """ Examine each pad of the module to determine
    the module's type
    """
    for pad in module.Pads():
        pad_attribute = pad.GetAttribute()
        if pad_attribute is not PN.PAD_ATTRIB_SMD:
            return False
    return True


def getFootprintRect(module, upright=True):
    """ module.GetFootprintRect() includes edge items
    in calculating bounding rectangle instead of the just the
    pads. This function does the module rectangle using
    only the pads. By default it calculates the true
    footprint size of the module before it was rotated.
    """
    area = PN.EDA_RECT()
    area.SetOrigin(module.GetPosition())
    area.SetEnd(module.GetPosition())
    rot_center = module.GetPosition()
    if upright:
        rot_angle = -(module.GetOrientation())
    else:
        rot_angle = 0
    for pad in module.Pads():
        pad_bb = pad.GetBoundingBox().GetBoundingBoxRotated(rot_center, rot_angle)  
        area.Merge(pad_bb)
    return area


def read_kicadpcb(kicadpcb_file):
    """ Open the board file, read the modules and extract the placement
    data.
    """
    board = PN.LoadBoard(kicadpcb_file)
    board_bb = board.ComputeBoundingBox(True)
    bot_left_x = board_bb.GetLeft()
    bot_left_y = board_bb.GetBottom()
    result_mods = {}
    for module in board.GetModules():
        rot = module.GetOrientation()/10.0
        module_rect = getFootprintRect(module, upright=True)
        x_size = PN.ToMils(module_rect.GetWidth())
        y_size = PN.ToMils(module_rect.GetHeight())
        designator = module.GetReference()
        module_center = module_rect.Centre()
        result_mods[designator] = {"DESIGNATOR": designator,
                                   "VALUE": module.GetValue(),
                                   "X_SIZE": x_size,
                                   "Y_SIZE": y_size,
                                   "ROTATION": rot,
                                   "SIDE": "top" if (module.GetLayer() is PN.F_Cu) else "bot",   #1/T/top for Top, 2/B/bot/bottom for Bottom
                                   "TYPE": "SMD" if (isModuleSMD(module)) else "PTH",            #1/SMT/SMD for SMD, 2 for PTH
                                   "X_LOC": PN.ToMils(module_center.x - bot_left_x),
                                   "Y_LOC": PN.ToMils(bot_left_y - module_center.y),
                                   "FOOTPRINT": "",                                              #C0805, R0603, TQFP-100
                                   "POPULATE": "1"                                               #1 for populate, 0 for do not populate
                                  }
    return result_mods


def read_net(net_file):
    with open(net_file, 'r') as ifile:
        ifile_lines = ifile.readlines()
    result_comps = {}
    found_comp = False
    brace_level = 0
    current_component = {"ref": None, "value":None, "part": None, "mpn": None}
    for line in ifile_lines:
        if ("(comp " in line) and (not found_comp):
            found_comp = True
        if found_comp:
            #print line.strip()
            if "(ref" in line:
                line_sep = line.split()
                current_component["ref"] = line_sep[2].strip(")").strip("(")
            elif "(part " in line:
                line_sep = line.split()
                current_component["part"] = line_sep[4].strip(")").strip("(")
            elif "(value " in line:
                line_sep = line.split()
                current_component["value"] = line_sep[1].strip(")").strip("(")
            elif "(name MPN" in line:
                line_sep = line.split()
                current_component["mpn"] = line_sep[3].strip(")").strip("(")
            for c in line:
                if c is "(":
                    brace_level += 1
                if c is ")":
                    brace_level -= 1
            if brace_level <= 0:
                #print current_component
                result_comps[current_component["ref"]] = {"part":current_component["part"], "value":current_component["value"], "mpn": current_component["mpn"]}
                current_component = {"ref": None, "value":None, "part": None, "mpn": None}
                found_comp = False
                brace_level = 0

    result_parts = {}
    found_part = False
    brace_level = 0
    current_part = {"part": None, "value":None, "mpn": None}
    for line in ifile_lines:
        if ("(libpart " in line) and (not found_part):
            found_part = True
        if found_part:
            #print line.strip()
            if "(part" in line:
                line_sep = line.split()
                current_part["part"] = line_sep[4].strip(")").strip("(")
            elif "(name Value" in line:
                line_sep = line.split()
                current_part["value"] = line_sep[3].strip(")").strip("(")
            elif "(name MPN" in line:
                line_sep = line.split()
                current_part["mpn"] = line_sep[3].strip(")").strip("(")
            for c in line:
                if c is "(":
                    brace_level += 1
                if c is ")":
                    brace_level -= 1
            if brace_level <= 0:
                #print current_part
                result_parts[current_part["part"]] = {"value":current_part["value"], "mpn":current_part["mpn"]}
                current_part = {"part": None, "value":None, "mpn": None}
                found_part = False
                brace_level = 0

    return result_comps, result_parts


def gen_xyrs(mods, comps, parts):
    result = []
    result.append("# Auto-generated for PCB")
    result.append("# DESIGNATOR	X_LOC	Y_LOC	ROTATION	SIDE	TYPE"
                   "	X_SIZE	Y_SIZE	VALUE	FOOTPRINT	POPULATE"
                   "	MPN	MPN1	MPN2	MPN3")

    refs = sorted(mods.keys())
    for r in sorted(refs):
        if mods[r]["VALUE"] != comps[r]["value"]:
            print("Error net value does not match pcb value for %s" % r)
            sys.exit(1)
        fragment = (("%(DESIGNATOR)s\t%(X_LOC)7.2f\t%(Y_LOC)7.2f\t%(ROTATION)7.1f\t%(SIDE)s\t%(TYPE)s\t"
                    "%(X_SIZE)7.2f\t%(Y_SIZE)7.2f\t %(VALUE)s\t%(FOOTPRINT)s\t%(POPULATE)s") % mods[r])
        row = [fragment]
        part = comps[r]["part"]
        if comps[r]["mpn"]:
            row.append(comps[r]["mpn"])
            row += [""]*3
        elif parts[part]["mpn"]:
            row.append(parts[part]["mpn"])
            row += [""]*3
        else:
            row += [""]*4
        result.append("\t".join(row))
    return "\n".join(result)


def main():
    parser = OptionParser("usage: gen_xyrs -i kicad_pcb file -o xyrs output file name.")
    parser.add_option("-i", "--input", dest="filename",
                      help="Input kicad_pcb FILE", metavar="FILE")
    parser.add_option("-o", "--output", dest="ofilename",
                      help="Output xyrs FILE", metavar="FILE")
    (options, args) = parser.parse_args()
    if not options.filename:
        parser.error("File .kicad_pcb file name is required.")
    if not options.ofilename:
        options.ofilename = options.filename.replace(".kicad_pcb", ".xyrs")
    mods = read_kicadpcb(options.filename)
    (comps, parts) = read_net(options.filename.replace(".kicad_pcb", ".net"))
    xyrs_table = gen_xyrs(mods, comps, parts)
    with open(options.ofilename, 'w') as ofile:
        ofile.write(xyrs_table)


if __name__ == '__main__':
    main()
