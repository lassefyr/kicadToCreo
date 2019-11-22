# https://github.com/latefyr/kicadcreo.git
# MIT license
#
# Parse Creo Schematic cable file and take harness numbers and
# wire/cable lengths back to Kicad schematic.
# 
# Do not overwrite the original Schematic. 
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
from xml.dom import minidom
import sys
import sch
import os

# Check that parameters exist for processing the file.

if len(sys.argv) < 2:
    print("Usage ", __file__, "<netlist.xml> <output file>", file=sys.stderr)
    sys.exit(1)

# Ignore netlist. Take the filename and change it to match the 
# expected creo schematic xml filename.
#
#netlist = kicad_netlist_reader.netlist(sys.argv[1])
creoSchXmlName = sys.argv[2]+"_creoin.xml"
kiCadOutputName = sys.argv[2]+"_creo.sch"
kiCadOriginalFile = sys.argv[2]+".sch"

#print (creoSchXmlName)	
#print (kiCadOutputName)	
#print (kiCadOriginalFile)	

if( os.path.isfile(creoSchXmlName) ):
	print ("Creo schematic inputfile OK :" + creoSchXmlName, file=sys.stdout)
else:
	print ("Creo schematic inputfile NOT FOUND \r" + creoSchXmlName, file=sys.stderr)
	sys.exit(1)
	
if( os.path.isfile(kiCadOriginalFile) ):
	print ("Kicad schematic inputfile OK :" + kiCadOriginalFile, file=sys.stdout)
else:
	print ("Kicad schematic inputfile NOT FOUND \r" + kiCadOriginalFile, file=sys.stderr)
	sys.exit(1)
	
	
creoXml = minidom.parse(creoSchXmlName)
connections = creoXml.getElementsByTagName("CONNECTION")
refDesVals = []
harnessNum = []
wireLength = []
for connection in connections:
	wireName = connection.getAttribute("name")
	type = connection.getAttribute("type")
	varName = ""
	varValue = ""
	if wireName[:1] =="W" or type == "ASSEMBLY":
		print(wireName)
		refDesVals.append(wireName)
		parameters = connection.getElementsByTagName('PARAMETER')
		for param in parameters:
			varName = param.getAttribute('name')
			varValue = param.getAttribute('value')
			if( varName == "LENGTH" ):
				wireLength.append(varValue)
				#print ("lenght = "+varValue)			
			if( varName == "HARNESS_NAME"):
				#print ("Cable Name = "+varValue)
				harnessNum.append(varValue)
			
# Put lenghts to Kicad Schematic
# Do not overwrite the original file
kiCadSch = sch.Schematic(kiCadOriginalFile)

for component in kiCadSch.components:
#{'name': 'Cabling:mx_43025-06', 'ref': 'J8'}
	for name, value in component.labels.items():
		#print("name = "+name+": value = "+value)	
		if value[:1]=="W" or value[:3]=="CBL":
			refDes=value
				#for name, value in component.fields[0].items():
			for field in component.fields:	
				for key in field.keys():
					# Get the component field "Length" and modify
					if field[key] == "\"Length\"":
						thisIsTheLengthParam = key
						print (key+"   "+ field[key])  
						print (field['ref'])
						try:
							myindex = refDesVals.index(refDes)
						except ValueError:
							print("Refdes \""+refDes+"\" does not exist! Not routed yet?", file=sys.stderr )
							continue
						# myindex = refDesVals.index(refDes)
						roundedWireLen = wireLength[myindex].split('.')[0]
						print("length for this wire is "+roundedWireLen+"mm")
						print("Harness is is "+harnessNum[myindex])
						field['ref'] = "\""+roundedWireLen+"mm\""
					# Get the component field "Harness_name" and modify
					if field[key] == "\"Harness_name\"":
						thisIsTheHarnName = key						
						try:
							myindex = refDesVals.index(refDes)						
						except ValueError:
							print("Refdes \""+refDes+"\" does not exist! Not routed yet?", file=sys.stderr )
							continue						
						harnessName = harnessNum[myindex]
						print("Harness is is "+harnessName)
						field['ref'] = "\""+harnessName+"\""
						
						
print( refDesVals )
print( wireLength )
print( harnessNum )
		
kiCadSch.save(kiCadOutputName)

