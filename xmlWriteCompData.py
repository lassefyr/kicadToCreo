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
		self.__infoString = ""
		self.__errorString = ""
		self.__warningString = ""	
        
        
	def writeCompData(self, netlist, outputFileName):

		isOutputFileOpended = False
		try:
			fout=open(outputFileName, "a")
			isOutputFileOpended = True
		except IOError:
			self.writeErrorStr("Error opening file -- filename = \""+outputFileName+"\"")
			fout = sys.stdout
		
		components = netlist.getInterestingComponents()
		
		for comp in components:
			refDes = comp.getRef()
			part = comp.getLibPart()

# Currently only components that are not W or CBL are allowed... You can have BTNxx, Relayxx, etc
			if refDes [:1] == "W" or refDes [:3] == "CBL":
				continue

			if (refDes.startswith("TUBE") or refDes.startswith("SHRINK") or refDes.startswith("TAPE")): 
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
				self.writeInfoStr("\""+refDes+"\" - Using Component Name as Modelname!\n")
			else:
				creoModel = self.CMP_USEVAL[0]
				
			if not creoModel:
				self.writeWarningStr(refDes+ " no Creo model name found!\n")
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
				self.writeErrorStr(""+refDes+", no pins found!")
		
# Component OBJ_TYPE Connector (Optional)-------------------------------------------------
			print("<PARAMETER name=\"OBJ_TYPE\" value=\"connector\" />", file = fout)			
# Component ATTACHED_TO_HARNESS don't know ------------------------------------------------
#			print("<PARAMETER name=\"ATTACHED_TO_HARNESS value=\"TRUE\" />", file = fout)

			if not self.CMP_USEVAL[7]:
				self.writeInfoStr("\""+refDes+"\" - No termName (Crimp) found!\n")
				#termName = "No terminal defined"
		
# Component PORT parameters for each pin  ------------------------------------------------
			forbiddenchars = set('!\"#$%&\'()*+,-./:;<=>?@[\\]^`{|}~.')
			for thisPin in pins.getChildren():
				print("<PORT name=\""+thisPin.get("pin", "num")+"\" physicalName=\""+thisPin.get("pin", "num")+"\" >", file = fout)
				print("<SYS_PARAMETER id=\"comp_"+refDes+"_"+thisPin.get("pin", "num")+"\" />", file = fout)
				
#				print("<PARAMETER name=\"PORT_TYPE\" value=\""+self.PORT_TYPE+"\" />", file = fout)	
				myPinName = (thisPin.get("pin", "name")).strip( )
				myPinName = myPinName.upper( )
				validPinName = True
				if ( any((c in forbiddenchars) for c in myPinName) ):
					validPinName = False
				if ( myPinName == "" or not validPinName ):
					myPinName = self.CMP_USEVAL[6]+thisPin.get("pin", "num")
					if( not validPinName ):
						self.writeWarningStr(refDes+ " Pin Name contains invalid characters: " + (thisPin.get("pin", "name")).strip( ) + " !\n" )
						self.writeWarningStr("Using default pin Name = " + myPinName + "\n" )
													
				print("<PARAMETER name=\"ENTRY_PORT\" value=\""+myPinName+"\" />", file = fout)
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

#-----------------------------------------------------------------------------------------
# String Logger functions
#
# These fuctions log the strings and outputs data to stdout and stderr
#
#-----------------------------------------------------------------------------------------		
	def writeInfoStr( self, iStr ):
		self.__infoString += iStr

	def getInfoStr( self ):
		return self.__infoString 

	def writeErrorStr( self, eStr ):
		self.__errorString += eStr
		
	def getErrorStr( self ):
		if self.__errorString == "":
			self.__errorString="No Errors!"		
		return self.__errorString 
		
	def clearErrorStr( self ):
		self.__errorString=""

	def writeWarningStr( self, wStr ):
		self.__warningString += wStr
		
	def getWarningStr( self ):
		if self.__warningString == "":
			self.__warningString="No Warnigns!"
		return self.__warningString 
		
	def clearWarningStr( self ):
		self.__warningString=""

