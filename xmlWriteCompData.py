#
# MIT license
#
# Part of kicadToCreo script
# This sample was created from one of the kicad bom scripts
# Write component data (connectors)
#
# Copyright (C) LasseFyr 2019.
#
# This has been tested only with Creo 4.0 070
#
"""
    @package
    Generate a net list file.

    Command line: 
    Run kicadToCreo script from Kicad eeschema with default parameters "%I" "%O"
"""

### Write out creo components
# Default values for values that are not with components
# or if definded as a truth.
from __future__ import print_function
import kicad_netlist_reader
import sys 

class xmlWriteCompData:
#   index               0           1              2             3              4             5            6             7
	CMP_PARAMS =   ["Modelname" ,"Layer"     ,"Num_of_pins" ,"Obj_type" , "Internal_len" ,"Grouping" ,"Entry_port" ,"Term_name" ]
	CMP_DEFAULTS = [""          ,"DEF_LINES" ,"0"           ,"connector", "5"            ,"round"    ,"PIN_"       ,""]
	
	CMP_USEVAL =   [""          ,""          ,""            ,""         , ""             ,""         ,""           ,""]
		  
	def __init__(self):
		self.ENTRY_PORT = "PIN_"
		self.PORT_TYPE = "Electrical"
		self.GROUPING = "round"	
		self.INTERNAL_LEN = "5"
		self.TERM_AUTO_ASSIGN = "TRUE"
		self.idNum = 1				# This is the first component
        
        
	def writeCompData(self, netlist, outputFileName):

		isOutputFileOpended = False
		try:
			fout=open(outputFileName, "a")
			isOutputFileOpended = True
		except IOError:
			print("Error opening file -- filename = \""+outputFileName+"\"", file=sys.stderr)
			fout = sys.stdout
		
		components = netlist.getInterestingComponents()
		
		for comp in components:
			refDes = comp.getRef()
			part = comp.getLibPart()

# Component currently only components starting with J are allowed 
# This can be changed to e.g. all cabling components allowed (refdes starts with cbl_XX##
# Where xx is the refdes (SPKR, J, BUTTON, SWITCH, etc 			
#			if refDes[:1] != "J":
			if refDes [:1] == "W" or refDes [:3] == "CBL":
				continue
			
			for listIndex in range(len(self.CMP_PARAMS)):
				tempStr =  comp.getField(self.CMP_PARAMS[listIndex])
				if tempStr:
					self.CMP_USEVAL[listIndex] =	tempStr
				else:
					self.CMP_USEVAL[listIndex] =	self.CMP_DEFAULTS[listIndex]
						
# Component COMPONENT --------------------------------------------------------------------
			if not self.CMP_USEVAL[0]:						
				creoModel = comp.getField("Value")
			if not creoModel:
				print(refDes+ " no Creo model name found!")
				creoModel = "NOT_DEFINED"
					
			print("<COMPONENT name=\""+refDes+"\" REFDES=\""+refDes+"\" subType=\"COMPONENT\" type=\"COMPONENT\" context=\"NONE\" modelName=\""+creoModel+"\" >", file = fout)

# Component SYS_PARAMETER ----------------------------------------------------------------								
			print("<SYS_PARAMETER id=\"comp_"+refDes+"\" />", file = fout)

# Component optional DESCRIPTION ---------------------------------------------------------
#			print("<PARAMETER name=\"DESCRIPTION\" value=\""+put your value parameter here+"\" />", file = fout)
						
# Component LAYER always DEF_LINES -------------------------------------------------------
			print("<PARAMETER name=\"LAYER\" value=\"DEF_LINES\" />", file = fout)
		
			pins = part.element.getChild('pins')

# Component NUM_OF_PINS how many pins in this component-----------------------------------					
			if pins:  #more than one
				howManyPins = len(pins.getChildren())
				print("<PARAMETER name=\"NUM_OF_PINS\" value=\""+str(howManyPins)+"\" />", file = fout)
			else:
				print(""+refDes+", no pins found!", file=sys.stderr)
		
# Component OBJ_TYPE Connector (Optional)-------------------------------------------------
			print("<PARAMETER name=\"OBJ_TYPE\" value=\"connector\" />", file = fout)			
# Component ATTACHED_TO_HARNESS don't know ------------------------------------------------
#			print("<PARAMETER name=\"ATTACHED_TO_HARNESS value=\"TRUE\" />", file = fout)

			if not self.CMP_USEVAL[7]:
				print("\""+refDes+"\" - No termName (Crimp) found!")
				#termName = "No terminal defined"
		
# Component PORT parameters for each pin  ------------------------------------------------
			for thisPin in pins.getChildren():
				print("<PORT name=\""+thisPin.get("pin", "num")+"\" physicalName=\""+thisPin.get("pin", "num")+"\" >", file = fout)
				print("<SYS_PARAMETER id=\"comp_"+refDes+"_"+thisPin.get("pin", "num")+"\" />", file = fout)
				
#				print("<PARAMETER name=\"PORT_TYPE\" value=\""+self.PORT_TYPE+"\" />", file = fout)	
				myPinName = thisPin.get("pin", "name")
				myPinName = myPinName.upper( )
				if ( myPinName == "" ):
					myPinName = self.CMP_USEVAL[6]+thisPin.get("pin", "num")
								
				print("<PARAMETER name=\"ENTRY_PORT\" value=\" "+myPinName+"\" />", file = fout)
				print("<PARAMETER name=\"SIGNAL_VALUE\" value=\"X\" />", file = fout)
				print("<PARAMETER name=\"GROUPING\" value=\""+self.CMP_USEVAL[5]+"\" />", file = fout)
				print("<PARAMETER name=\"LAYER\" value=\"DEF_LINES\" />", file = fout)					
				print("<PARAMETER name=\"INTERNAL_LEN\" value=\""+self.CMP_USEVAL[4]+"\" />", file = fout)
			
				if self.CMP_USEVAL[7]:
					print("<PARAMETER name=\"TERM_NAME\" value=\""+self.CMP_USEVAL[7]+"\" />", file = fout)
					print("<PARAMETER name=\"TERM_AUTO_ASSIGN\" value=\"TRUE\" />", file = fout)
				print("</PORT>", file = fout)
# Component end PORT parameters for each pin  ------------------------------------------------
			
			print("</COMPONENT>", file = fout)
		
		if isOutputFileOpended == True:
			fout.close()
			isOutputFileOpended = False
