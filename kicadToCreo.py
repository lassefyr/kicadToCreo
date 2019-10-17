# https://github.com/latefyr/kicadcreo.git
# MIT license
#
# Parse kicad netlist to creo harness xml
# This sample was created from one of the kicad bom scripts
#
# Copyright (C) LasseFyr 2019.
#
# This has been tested only with Creo 4.0 070
#
"""
    @package
    Generate a net list file.

    Command line: 
    Run from Kicad eeschema with default parameters "%I" "%O"
"""

from __future__ import print_function

#import os
# Import the KiCad python helper module
import kicad_netlist_reader
import sys
import xmlWriteCompData
import xmlWriteSpools
import xmlWriteConnections


if len(sys.argv) < 2:
    print("Usage ", __file__, "<netlist.xml> <output file>", file=sys.stderr)
    sys.exit(1)


# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop
netlist = kicad_netlist_reader.netlist(sys.argv[1])
creoLogicalFileName = sys.argv[2]+"_creo.xml"

# Open a file to write to, if the file cannot be opened output to stdout
# instead
isOutputFileOpended = False
if len(creoLogicalFileName) > 2:
	try:
		fout = open(creoLogicalFileName, 'w')
		isOutputFileOpended = True
	except IOError:
		e = "Can't open output file for writing: " + creoLogicalFileName
		print( __file__, ":", e, sys.stderr )
		fout = sys.stdout
else:
	fout = sys.stdout
    	
		
# Generate a YAML style netlist
components = netlist.getInterestingComponents()

print("<?xml version=\"1.0\"?>", file = fout)
print("<!DOCTYPE rsData SYSTEM \"rsData_v2.dtd\">", file = fout)
print("<rsData>", file = fout)
print("<HEADER dtdVersion=\"2.0\"", file = fout)
print("        creator=\"KICAD\"", file = fout)
print("        createdByApplication=\"Kicad Schematic\"", file = fout)
print("        owner=\"Kicad\"", file = fout)
print("        contents=\"DOCUMENT\"", file = fout)
print("        diagramType=\"WIRING\"", file = fout)
print("        documentName=\""+sys.argv[1]+"\"", file = fout)
print("        documentFolder=\"Design/wiring\"        />", file = fout)
        
	
if isOutputFileOpended == True:
	fout.close()
	isOutputFileOpended = False		


components = xmlWriteCompData.xmlWriteCompData()
components.writeCompData(netlist,creoLogicalFileName)

spools = xmlWriteSpools.xmlWriteSpools()
spools.writeSpoolData(netlist,creoLogicalFileName)

connections = xmlWriteConnections.xmlWriteConnections(spools)
connections.writeConnections(netlist,creoLogicalFileName)


isOutputFileOpended = False
if len(creoLogicalFileName) > 2:
	try:
		fout = open(creoLogicalFileName, 'a')
		isOutputFileOpended = True
	except IOError:
		e = "Can't open output file for writing: " + creoLogicalFileName
		print( __file__, ":", e, sys.stderr )
		fout = sys.stdout
else:
	fout = sys.stdout

print("</rsData>", file = fout)

if isOutputFileOpended == True:
	fout.close()
	isOutputFileOpended = False	
