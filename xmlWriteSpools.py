#
# MIT license
#
# Part of kicadToCreo script
# This sample was created from one of the kicad bom scripts
# Write spool data (cables)
# ToDo: Add tape, shrink, tube spools 
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


from __future__ import print_function
import kicad_netlist_reader
import sys 

class xmlWriteSpools:
	_CBL_PARAMS =   ["Value"      ,"color","Num_conductors","Thickness","Density","Min_bend_radius","Sub_thickness","Vendor"   ,"Vendor_pn"   ,"Type"]
	_CBL_DEFAULTS = ["NOT_DEFINED","Gray" ,"0"             ,"4.5"      ,"2.0e-5" ,"1"              ,"2.0"          ,"No Vendor","No Vendor_pn","prefab"]

	def __init__(self):
		self.SP_T1 = "NORMAL_SPOOL" 		#for master spool
		self.SUB_SP= "WIRE_SPOOL"
		self.SP_T2 = "INLINE_SPOOL"			#for the wires inside a spool
		self.DEF_COLOR = "GRAY"
		self.MIN_BEND = "5"
		self.MIN_THICKNESS = "1"			#In millimeters
		self.idNum = 1						# This is the first component    
		self.__spoolData = ""
		self.cblSpoolName = []
		self.cblSpoolId = []
		self.__errorString = ""
		self.__warningString=""	
        
	def writeSpoolData(self, netlist, outputFileName):
		isOutputFileOpen = False
		try:
			if sys.version_info.major < 3:		
				fout = open(outputFileName, "a")
			else:
				fout = open(outputFileName, "a", encoding='utf-8')								
			isOutputFileOpen = True
		except IOError:
			self.writeErrorStr("Error opening file -- filename = \""+outputFileName+"\"")
			fout = sys.stdout
		print("\n<!--Spools-->\n", file = fout)		
		
		components = netlist.getInterestingComponents()
		
		# Write individual spool data (single wires)
		self.writeWireSpool(components)
		print(self.__spoolData, file = fout)

		# Zero the array before otherSpool. Other spools are the tubes, shrinks and tape.
		self.__spoolData = ""
		self.writeOtherSpool(components)
		#print(self.__spoolData, file = fout)
		fout.write(self.__spoolData)

		# Zero the array before CblSpool and write cables (multiple conductor cables with sheath)
		self.__spoolData = ""
		self.writeCblSpool(components)
		#print(self.__spoolData, file = fout)
		fout.write(self.__spoolData)
		
		if isOutputFileOpen == True:
			fout.close()
			isOutputFileOpen = False						
				
#-----------------------------------------------------------------------------------------
# def writeCblSpool(self, components ):
#
# Write spool data for Cables
# Quick and dirty Cable spool data write
#-----------------------------------------------------------------------------------------
	def writeCblSpool(self, components ):
		spoolList = []						# Spool list is empty
		condIdIndex = 1						# This is used for spool indices
		for comp in components:
			refDes = comp.getRef()
			part = comp.getLibPart()
			description = comp.getDescription()
			
			if refDes[:3] != "CBL":
				continue
			
			spoolName = comp.getField("Value")
			
			if not spoolName:
				self.writeErrorStr(refDes+ " no Spool name defined!")
				spoolName = "NOT_DEFINED"
				continue

#			self.writeWarningStr("writing " + refDes)

# Check if Spool has been processed ------------------------------------------------------
			exitCompInComponentsLoop = False			
			for thisSpool in spoolList:
				if thisSpool == spoolName:
					exitCompInComponentsLoop = True
			if exitCompInComponentsLoop == True:
				continue
			spoolList.append(spoolName)
								
# Component NUM_OF_PINS how many pins in this component-----------------------------------								
			pins = part.element.getChild("pins")
			if pins:   # more than one
				howManyPins = len(pins.getChildren())
				#print("Pins "+str(howManyPins))
			else:		# no Pins continue	
				continue

			colorTable  = []
			awgTable    = []
			thicknessTable = []			
			
			for i in range(1, int(howManyPins/2+1)):	#(each net has two counter parts)
				spoolColor = ""				
				spoolAwg = comp.getField("Gauge")		# Returns empty string if filed does not exist				
				spoolThickness = ""
								
				wireColor = comp.getField("color"+str(i))
				wireColor = wireColor.replace(" ", "") 	# Remove Spaces
				splitWireColor = wireColor.split(",")	# Split string comma separated							
				splitLen = len( splitWireColor )		# How Many Strings
				
				if splitLen == 0:  
					spoolColor		= "Gray"
				if splitLen >= 1: 
					spoolColor 		= splitWireColor[0]
				if splitLen >= 2:
					if splitWireColor[1]:
						spoolAwg 	= splitWireColor[1]	# If this exists then use this new Gauge
				if splitLen >= 3: 
					spoolThickness 	= splitWireColor[2]
				
				colorTable.append( spoolColor )
				awgTable.append( spoolAwg )
				thicknessTable.append( spoolThickness )														
				
			numOfCoductors = comp.getField("Num_conductors")
			if int(numOfCoductors) != int(howManyPins/2):
				self.writeErrorStr( "FATAL: Spool = " + refDes + "\n" )
				self.writeErrorStr( "Num_conductors different from Numofpins/2 Pin="+ numOfCoductors+ "\n")
			
			thickness = comp.getField("Thickness")
			if not thickness:
				thickness = "4.5"

			mainColor  = comp.getField("Color")
			if not mainColor:
				mainColor = "Gray"
									
			density  = comp.getField("Density")
			if not density:
				density = "2.0e-5"

			minBendRadius  = comp.getField("Min_bend_radius")
			if not minBendRadius:
				minBendRadius = "1"

			subThickness  = comp.getField("Sub_thickness")
			if not subThickness:
				subThickness = "2.0"

			vendor  = comp.getField("Vendor")
			if not vendor:
				vendor = "No Vendor"

			vendorPn  = comp.getField("Vendor_pn")
			if not vendorPn:
				vendorPn = "No Vendor Part No."

			type  = comp.getField("Type")
			if not type:
				type = "prefab"
			spoolSubType = "\"CABLE_SPOOL\""
			if type.lower() == "ribbon":
				spoolSubType = "\"RIBBON_SPOOL\""
			
			self.__spoolData += "<SPOOL name=\""+spoolName+"\" type=\"NORMAL_SPOOL\" subType="+spoolSubType+" >\n"
			self.__spoolData += "<SYS_PARAMETER id=\"cbl_"+spoolName+"\" />\n"									
			self.__spoolData += "<PARAMETER name=\"UNITS\" value=\"MM\" />\n"
			self.__spoolData += "<PARAMETER name=\"OBJ_TYPE\" value=\"CABLE\" />\n"			
			self.__spoolData += "<PARAMETER name=\"MIN_BEND_RADIUS\" value=\""+minBendRadius+"\" />\n"	
			if type.lower() == "ribbon":
				self.__spoolData += "<PARAMETER name=\"BEND_RADIUS\" value=\"\" />\n" # This was added to Ribbon spools so that the Creo Compare won't give an error
			self.__spoolData += "<PARAMETER name=\"THICKNESS\" value=\""+thickness+"\" />\n"
			self.__spoolData += "<PARAMETER name=\"NUM_COND\" value=\""+numOfCoductors+"\" />\n"	
			self.__spoolData += "<PARAMETER name=\"DENSITY\" value=\""+density+"\" />\n"					
			self.__spoolData += "<PARAMETER name=\"MASS_UNITS\" value=\"KG\" />\n"	
			self.__spoolData += "<PARAMETER name=\"COLOR\" value=\""+mainColor+"\" />\n"
			self.__spoolData += "<PARAMETER name=\"VENDOR\" value=\""+vendor+"\" />\n"								
			self.__spoolData += "<PARAMETER name=\"VENDOR_PN\" value=\""+vendorPn+"\" />\n"
			if description:
				self.__spoolData += "<PARAMETER name=\"SPECIFICATION\" value=\""+description+"\" />\n"

			firstSpoolIndex = condIdIndex
			for i in range(1, int(howManyPins/2+1)): #(each net has two counter parts)
				self.__spoolData += "<CONDUCTOR id=\"cond_"+str(condIdIndex)+"\" name=\""+spoolName+"-"+str(i)+"\" spoolID=\"sp"+str(condIdIndex)+"\" />\n"
				self.pushCblSpoolId((spoolName+"-"+str(i)), condIdIndex)
				condIdIndex+=1
			self.__spoolData += "</SPOOL>\n"
			
			#print ("range is " + str(int(howManyPins/2)))
			
			for i in range(1, int(howManyPins/2+1)): #(each net has two counter parts)
				self.__spoolData += "<SPOOL name=\""+spoolName+":"+str(i)+"\" type=\"INLINE_SPOOL\" subType=\"WIRE_SPOOL\" >\n"
				self.__spoolData += "<SYS_PARAMETER id=\"sp"+str(firstSpoolIndex)+"\" />\n"	
				self.__spoolData += "<PARAMETER name=\"COLOR\" value=\""+(colorTable[(i-1)].lower())+"\" />\n"		# lowercase Just in case CS172530
				self.__spoolData += "<PARAMETER name=\"COND_ID\" value=\""+str(i)+"\" />\n"
				self.__spoolData += "<PARAMETER name=\"MIN_BEND_RADIUS\" value=\""+minBendRadius+"\" />\n"				
				self.__spoolData += "<PARAMETER name=\"UNITS\" value=\"MM\" />\n"
				if( thicknessTable[(i-1)] ):
					self.__spoolData += "<PARAMETER name=\"THICKNESS\" value=\""+thicknessTable[(i-1)]+"\" />\n"
				else:
					self.__spoolData += "<PARAMETER name=\"THICKNESS\" value=\""+subThickness+"\" />\n"
				if( awgTable[(i-1)] ):
					self.__spoolData += "<PARAMETER name=\"WIRE_GAUGE\" value=\""+awgTable[(i-1)]+"\" />\n"
				self.__spoolData += "</SPOOL>\n"
				firstSpoolIndex+=1
												

	def pushCblSpoolId(self, spoolName, spoolNumber):
		self.cblSpoolName.append(spoolName)
		self.cblSpoolId.append(spoolNumber)
	
	def printCblSpoolNames(self):
		# print(self.cblSpoolName)
		if not self.cblSpoolName:
			return( "No Multi-Conductor Cable Spools" )
		return self.cblSpoolName

	def getCblSpoolId(self, spoolName):
		try:
			myInt = self.cblSpoolName.index(spoolName)
		except ValueError:
			return -1
	
		return myInt
	
#-----------------------------------------------------------------------------------------
# def writeWireSpool(self, components ):
#
# Write spool data for Wires
# Quick and dirty Spool data for wires
#-----------------------------------------------------------------------------------------
	def writeWireSpool(self, components ):
		spoolList = []				# Spool list is empty
		for comp in components:
			refDes = comp.getRef()
			part = comp.getLibPart()
			description = comp.getDescription()
			
			if refDes[:1] != "W":
				continue
			
			spoolName = comp.getField("Value")
			if not spoolName:
				self.writeWarningStr(refDes+ " no Spool name defined!")
				spoolName = "NOT_DEFINED"
				continue

# Check if Spool has been processed ------------------------------------------------------
			exitCompInComponentsLoop = False			
			for thisSpool in spoolList:
				if thisSpool == spoolName:
					exitCompInComponentsLoop = True
			if exitCompInComponentsLoop == True:
				continue
			spoolList.append(spoolName)
					
					
			self.__spoolData += "<SPOOL name=\""+spoolName+"\" type=\""+self.SP_T1+"\" subType=\""+self.SUB_SP+"\" >\n"
			self.__spoolData += "<SYS_PARAMETER id=\"w_"+spoolName+"\" />\n"

# Wire COLOR -----------------------------------------------------------------------------			
			spoolColor = comp.getField("Color").lower()
			if not spoolColor:
				self.writeWarningStr("No Spool color defined for "+spoolName)
				spoolColor = self.DEF_COLOR.lower()
			self.__spoolData += "<PARAMETER name=\"COLOR\" value=\""+spoolColor+"\" />\n"
# Wire DENSITY ---------------------------------------------------------------------------			
			density = comp.getField("Density")
			if not density:
				self.writeWarningStr("No Density for wire "+spoolName+" defined!")
			else:
				self.__spoolData += "<PARAMETER name=\"DENSITY\" value=\""+density+"\" />\n"
				self.__spoolData += "<PARAMETER name=\"MASS_UNITS\" value=\"KG\" />\n"

# Wire MIN_BEND_RADIUS -------------------------------------------------------------------			
			minBend = comp.getField("Min_bend_radius")
			if not minBend:
				self.writeWarningStr("No minimum bend radius defined!")
				minBend = self.MIN_BEND
			self.__spoolData += "<PARAMETER name=\"MIN_BEND_RADIUS\" value=\""+minBend+"\" />\n"

# Wire TYPE (always wire)-----------------------------------------------------------------						
			self.__spoolData += "<PARAMETER name=\"OBJ_TYPE\" value=\"WIRE\" />\n"

# Wire THICKNESS -------------------------------------------------------------------------									
			thickness = comp.getField("Thickness")
			if not thickness:
				self.writeWarningStr("No Thickness defined!")
				thickness = self.MIN_THICKNESS
			self.__spoolData += "<PARAMETER name=\"THICKNESS\" value=\""+thickness+"\" />\n"

# Wire UNITS (default to mm)--------------------------------------------------------------															
			self.__spoolData += "<PARAMETER name=\"UNITS\" value=\"MM\" />\n"

# Wire WIRE_GAUGE (Optional) -------------------------------------------------------------															
			gauge = comp.getField("Gauge")
			if not gauge:
				self.writeWarningStr("No Gauge for "+spoolName+" defined!")
			else:
				self.__spoolData += "<PARAMETER name=\"WIRE_GAUGE\" value=\""+gauge+"\" />\n"

# Wire USER_PARAMETERS (Vendor and Vendor_pn) --------------------------------------------															
			user_parameter = comp.getField("Vendor")
			if user_parameter:
				self.__spoolData += "<PARAMETER name=\"VENDOR\" value=\""+user_parameter+"\" />\n"
			user_parameter = comp.getField("Vendor_pn")
			if user_parameter:
				self.__spoolData += "<PARAMETER name=\"VENDOR_PN\" value=\""+user_parameter+"\" />\n"
			
# Wire USER_PARAMETERS (Specification) ---------------------------------------------------															
			if description:
				self.__spoolData += "<PARAMETER name=\"SPECIFICATION\" value=\""+description+"\" />\n"
			
# Wire END SPOOL DEFINE ------------------------------------------------------------------																					
			self.__spoolData += "</SPOOL>\n"
			
			
#-----------------------------------------------------------------------------------------
# def writeOtherSpool(self, components ):
#
# Write spool data for Tubes, Tapes, and Shrinks
# There seems to be some issues when reading the Sheath spool types
# 
# With type parameter I was able to get the type to be "Sheath"
# but the diameters become "0"
#
#
# MORE FROM PTC:
# Sheath type spools are exported to NWF as cable spool and to XML as wire in Creo Parametric
# Creo Parametric 4.0 to 6.0
# Created: 21-Aug-2019   |   Modified: 21-Aug-2019   
# Sheath type spools are exported to NWF as cable spool and to XML as wire in Creo Parametric 
#
#   Sheath type spools are exported to NWF as cable spool and to XML as wire
#	When importing .nwf file the parameter spool TYPE changed it's value from SHEATH to PREFAB
#
#	Resolution:
#		Reported to R&D as SPR 7732529
#	Workaround:
#		Load the .nwf file, save the ribbon spool to .spl file
#		Change the parameter TYPE in the spl file to SHEATH
#		Load the .spl file (overwrite the existing spool).
#
#-----------------------------------------------------------------------------------------
	def writeOtherSpool(self, components ):
		spoolList = []				# Spool list is empty
		for comp in components:
			refDes = comp.getRef()
			part = comp.getLibPart()
			description = comp.getDescription()
			
			if not (refDes.startswith("TUBE") or refDes.startswith("SHRINK") or refDes.startswith("TAPE")): 
				continue
			
			spoolName = comp.getField("Value")
			if not spoolName:
				self.writeWarningStr(refDes+ " no Spool name defined!")
				spoolName = "NOT_DEFINED"
				continue

# Check if Spool has been processed ------------------------------------------------------
			exitCompInComponentsLoop = False			
			for thisSpool in spoolList:
				if thisSpool == spoolName:
					exitCompInComponentsLoop = True
			if exitCompInComponentsLoop == True:
				continue
			spoolList.append(spoolName)
					
					
			self.__spoolData += "<SPOOL name=\""+spoolName+"\" type=\"NORMAL_SPOOL\" subType=\"SHEATH_SPOOL\" >\n"
			self.__spoolData += "<SYS_PARAMETER id=\"Sh_"+spoolName+"\" />\n"

# Sheath TYPE (Shrink, Tube, or Tape) ----------------------------------------------------						
			self.__spoolData += "<PARAMETER name=\"TYPE\" value=\"SHEATH\" />\n"			

			sheathType = comp.getField("Sheath_type")
			sheathType = sheathType.upper()
			if not sheathType:
				self.writeWarningStr("No Sheath Type defined for "+refDes+"!")
				sheathType = "TUBE"
			self.__spoolData += "<PARAMETER name=\"SHEATH_TYPE\" value=\""+sheathType+"\" />\n"

# Sheath WALL THICKNESS -------------------------------------------------------------------------									
			thickness = comp.getField("Wall_Thickness")
			if not thickness:
				self.writeWarningStr("No Wall Thickness defined for "+refDes+"! Using default value = 1")
				thickness = "1"
			self.__spoolData += "<PARAMETER name=\"WALL_THICKNESS\" value=\""+thickness+"\" />\n"

# Sheath COLOR -----------------------------------------------------------------------------			
			spoolColor = comp.getField("Color").lower()
			if not spoolColor:
				self.writeWarningStr("No Spool color defined for "+spoolName)
				spoolColor = self.DEF_COLOR.lower()
			self.__spoolData += "<PARAMETER name=\"COLOR\" value=\""+spoolColor+"\" />\n"

# Sheath MIN_BEND_RADIUS -------------------------------------------------------------------			
			minBend = comp.getField("Min_bend_radius")
			if not minBend:
				self.writeWarningStr("No minimum bend radius defined for "+spoolName)
				minBend = self.MIN_BEND
			self.__spoolData += "<PARAMETER name=\"MIN_BEND_RADIUS\" value=\""+minBend+"\" />\n"

# Sheath UNITS (default to mm)--------------------------------------------------------------															
			self.__spoolData += "<PARAMETER name=\"UNITS\" value=\"MM\" />\n"

# Sheath Inner Diameter  -------------------------------------------------------------------
			innerDiam = comp.getField("Preshrink_inner_diameter")
			if not innerDiam:
				self.writeWarningStr("No Inned Diameter defined for " + refDes+"!")
				innerDiam = "10"
			self.__spoolData += "<PARAMETER name=\"PRESHRINK_INNER_DIAMETER\" value=\""+innerDiam+"\" />\n"

# Sheath Outer Diameter  -------------------------------------------------------------------
			outerDiam = comp.getField("Outer_Diameter")
			if not outerDiam:
				self.writeWarningStr("No Outer Diameter defined for " + refDes+"!")
				innerDiam = "11"
			if float(innerDiam) >= float(outerDiam):
				self.writeWarningStr("Inner diameter larger than Outer diameter for " + refDes+"!")
				outerDiam = "{:.1f}".format(float(innerDiam)+1)
				#outerDiam = f"{(float(innerDiam)+1):.1f}"
				
			self.__spoolData += "<PARAMETER name=\"OUTER_DIAMETER\" value=\""+outerDiam+"\" />\n"

# Sheath USER_PARAMETERS (Vendor and Vendor_pn) --------------------------------------------															
			user_parameter = comp.getField("Vendor")
			if user_parameter:
				self.__spoolData += "<PARAMETER name=\"VENDOR\" value=\""+user_parameter+"\" />\n"
			user_parameter = comp.getField("Vendor_pn")
			if user_parameter:
				self.__spoolData += "<PARAMETER name=\"VENDOR_PN\" value=\""+user_parameter+"\" />\n"
			
# Sheath USER_PARAMETERS (Specification) ---------------------------------------------------															
			if description:
				self.__spoolData += "<PARAMETER name=\"SPECIFICATION\" value=\""+description+"\" />\n"
			
# Sheath END SPOOL DEFINE ------------------------------------------------------------------															
			self.__spoolData += "</SPOOL>\n"

#-----------------------------------------------------------------------------------------
# String Logger functions
#
# These fuctions log the strings and outputs data to stdout and stderr
#
#-----------------------------------------------------------------------------------------		
	def writeErrorStr( self, eStr ):
		self.__errorString += eStr
		
	def getErrorStr( self ):
		if self.__errorString == "":
			self.__errorString="Spools: No Errors!"
		return self.__errorString 
		
	def clearErrorStr( self ):
		self.__errorString=""

	def writeWarningStr( self, wStr ):
		self.__warningString += wStr
		
	def getWarningStr( self ):
		if self.__warningString == "":
			self.__warningString="Spools: No Warnigns!"
		return self.__warningString 
		
	def clearWarningStr( self ):
		self.__warningString=""						

