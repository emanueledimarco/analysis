#!/usr/bin/env python

import os,math
import numpy as np

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module

from snakes import SnakesFactory

class ImagesAnalyzer:

    def __init__(self,rfile,options,modules=[]):
        self.rebin = options.rebin 
        self.rfile = rfile
        self.options = options
        self.modules = modules
        self.cutFile = options.cutFile
        self.pedfile_name = '{base}_ped_rebin{rb}.root'.format(base=os.path.splitext(self.rfile)[0],rb=self.rebin)
        if not options.calcPedestals and not os.path.exists(self.pedfile_name):
            print "WARNING: pedestal file ",self.pedfile_name, " not existing. First calculate them..."
            self.calcPedestal(options.numPedEvents)
        print "Pulling pedestals..."
        pedrf = ROOT.TFile.Open(self.pedfile_name)
        self.pedmap = pedrf.Get('pedmap').Clone()
        self.pedmap.SetDirectory(None)
        self.pedmean = pedrf.Get('pedmean').GetMean()
        self.pedrms = pedrf.Get('pedrms').GetMean()
        pedrf.Close()

    def zs(self,th2):
        nx = th2.GetNbinsX(); ny = th2.GetNbinsY();
        th2_zs = ROOT.TH2D(th2.GetName()+'_zs',th2.GetName()+'_zs',nx,0,nx,ny,0,ny)
        th2_zs.SetDirectory(None)
        for ix in xrange(1,nx+1):
            for iy in xrange(1,ny+1):
                if not self.isGoodChannel(ix,iy): continue
                ped = self.pedmap.GetBinContent(ix,iy)
                noise = self.pedmap.GetBinError(ix,iy)
                z = max(th2.GetBinContent(ix,iy)-ped,0)
                if z>5*noise: th2_zs.SetBinContent(ix,iy,z)
                #print "x,y,z=",ix," ",iy," ",z,"   3*noise = ",3*noise
        th2_zs.GetZaxis().SetRangeUser(0,1)
        return th2_zs

    def isGoodChannel(self,ix,iy):
        pedval = self.pedmap.GetBinContent(ix,iy)
        pedrms = self.pedmap.GetBinError(ix,iy)
        if pedval > 110: return False
        if pedrms < 0.2: return False
        if pedrms > 5: return False
        return True

    def run(self):
        if len(self.modules) == 0: 
	    raise RuntimeError("Running with no modules does nothing!")

        outname = self.options.plotDir
        print "outname = ",outname, "   ",os.path.dirname(outname)
        if outname and not os.path.exists(outname):
            os.system("mkdir -p "+outname)
            os.system("cp ~/cernbox/www/Cygnus/index.php "+outname)
            
        tf = ROOT.TFile.Open(self.rfile)
        c1 = ROOT.TCanvas('c1','',600,600)

        for m in self.modules: m.beginJob()
        
        (nproc, time) = eventLoop(self.modules,self.options)

        for m in self.modules: m.endJob()

            
        ROOT.gStyle.SetOptStat(0)
        ROOT.gStyle.SetPalette(ROOT.kRainBow)
        # loop over events (pictures)
        for ie,e in enumerate(tf.GetListOfKeys()) :
            if ie==options.maxEntries: break
            name=e.GetName()
            obj=e.ReadObj()
            if not obj.InheritsFrom('TH2'): continue
            print "Processing histogram: ",name
            obj.RebinX(self.rebin); obj.RebinY(self.rebin)
            obj.Scale(1./float(math.pow(self.rebin,2)))
            h2zs = self.zs(obj)

            print "Analyzing its contours..."
            snfac = SnakesFactory(h2zs,name,options)
            snfac.getClusters()

            #snakes = snfac.getContours(iterations=100)
            #snfac.plotContours(snakes,fill=True)
            #snfac.filledSnakes(snakes)
            
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
    p=ImagesAnalyzer(options,args,modules)
                     
    if options.calcPedestals:
        ana.calcPedestal(options.numPedEvents)
    ana.reconstruct()
