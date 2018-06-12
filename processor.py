#!/usr/bin/env python

import os,sys
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from framework.analysis import ImagesAnalyzer


if __name__ == '__main__':

    from optparse import OptionParser
    parser = OptionParser(usage='%prog h5file1,...,h5fileN [opts] ')
    parser.add_option('-r', '--rebin', dest='rebin', default=4, type='int', help='Rebin factor (same in x and y)')
    parser.add_option('-p', '--pedestal', dest='calcPedestals', default=False, action='store_true', help='First calculate the pedestals')
    parser.add_option(      '--numPedEvents', dest='numPedEvents', default=-1, type='float', help='Use the last n events to calculate the pedestal. Default is all events')

    parser.add_option(      '--max-entries', dest='maxEntries', default=-1, type='float', help='Process only the first n entries')
    parser.add_option(      '--pdir', dest='plotDir', default='./', type='string', help='Directory where to put the plots')

    (options, args) = parser.parse_args()

    inputf = args[0]
    ana = analysis(inputf,options)
    print "Will save plots to ",options.plotDir

    modules = []
    imports = globals()[options.moduleList] + options.imports
    for mod, names in imports:
        import_module(mod)
        obj = sys.modules[mod]
        selnames = names.split(",")
        for name in dir(obj):
            if name[0] == "_": continue
            if name in selnames:
                print "Loading %s from %s " % (name, mod)
                modules.append(getattr(obj,name)())
    p=ImagesAnalyzer(inputf,options,modules)
                     
    if options.calcPedestals:
        ana.calcPedestal(options.numPedEvents)
    ana.reconstruct()
