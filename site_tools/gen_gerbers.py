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


def gen_gerbers(filename, plot_folder):
    board = PN.LoadBoard(filename)

    pc = PN.PLOT_CONTROLLER(board)
    po = pc.GetPlotOptions()
    po.SetOutputDirectory(plot_folder)

    # Set some important plot options:
    po.SetPlotFrameRef(False)
    po.SetLineWidth(PN.FromMM(0.15))
    po.SetAutoScale(False)
    po.SetScale(1)
    po.SetMirror(False)
    po.SetUseGerberAttributes(False)
    po.SetUseGerberProtelExtensions(True)
    po.SetExcludeEdgeLayer(True)
    po.SetScale(1)
    po.SetUseAuxOrigin(False)
    po.SetSubtractMaskFromSilk(False)
    po.SetPlotReference(True)
    po.SetPlotValue(False)

    layers = [
        ( "F.Cu",       PN.F_Cu,      "Top layer" ),
        ( "B.Cu",       PN.B_Cu,      "Bottom layer" ),
        ( "B.Paste",    PN.B_Paste,   "Paste Bottom" ),
        ( "F.Paste",    PN.F_Paste,   "Paste top" ),
        ( "F.SilkS",    PN.F_SilkS,   "Silk top" ),
        ( "B.SilkS",    PN.B_SilkS,   "Silk top" ),
        ( "B.Mask",     PN.B_Mask,    "Mask bottom" ),
        ( "F.Mask",     PN.F_Mask,    "Mask top" ),
        ( "Edge.Cuts",  PN.Edge_Cuts, "Edges" ),
    ]

    for layer_prefix, layer_id, layer_info in layers:
        pc.SetLayer(layer_id)
        pc.OpenPlotfile(layer_prefix, PN.PLOT_FORMAT_GERBER, layer_info)
        print('Plot %s' % os.path.basename(pc.GetPlotFileName()))
        if pc.PlotLayer() == False:
            print("Plot error while generating %s" % layer_info)
            sys.exit(1)
    pc.ClosePlot()

    # Generate the drill file
    drl = PN.EXCELLON_WRITER(board)
    drl.SetMapFileFormat(PN.PLOT_FORMAT_GERBER)
    mirror = False
    minimal_header = False
    offset = PN.wxPoint(0,0)
    mergeNPTH = True
    drl.SetOptions(mirror, minimal_header, offset, mergeNPTH)
    metric_fmt = False
    zeros_fmt = PN.EXCELLON_WRITER.SUPPRESS_LEADING
    left_digits = 2
    right_digits = 4
    drl.SetFormat(metric_fmt, zeros_fmt, left_digits, right_digits)
    generate_drl = True
    generate_map = True
    print("Create drill and map files")
    drl.CreateDrillandMapFilesSet(pc.GetPlotDirName(), generate_drl, generate_map)


def main():
    parser = OptionParser("usage: gen_gerbers -i kicad_pcb_file [-o gerber_output_folder]")
    parser.add_option("-i", "--input", dest="filename",
                      help="Input kicad_pcb FILE", metavar="FILE")
    parser.add_option("-o", "--output_dir", dest="output_dir", default="./gerbers",
                      help="Output DIR for the gerber files", metavar="DIR")
    (options, args) = parser.parse_args()
    if not options.filename:
        parser.error("File .kicad_pcb file name is required.")

    gen_gerbers(options.filename, options.output_dir)

 
if __name__ == "__main__":
    main()
