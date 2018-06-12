#!/usr/bin/env python

import math
import ROOT

class Module:
    def __init__(self):
        pass
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def analyze(self, th2):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        pass

def eventLoop(modules, inputFile, options):
    t0 = time.clock(); tlast = t0; doneEvents = 0;
    
    # loop over events (pictures)
    for ie,e in enumerate(tf.GetListOfKeys()) :
        if ie==options.maxEntries: break
        name=e.GetName()
        obj=e.ReadObj()
        if not obj.InheritsFrom('TH2'): continue
        print "Processing histogram: ",name
        obj.RebinX(options.rebin); obj.RebinY(options.rebin)
        obj.Scale(1./float(math.pow(self.rebin,2)))

        doneEvents += 1
        ret = True
        
        for m in modules: 
            ret,th2 = m.analyze(th2) 
            if not ret: break
        if ret:
            acceptedEvents += 1

    return (doneEvents, time.clock() - t0)
