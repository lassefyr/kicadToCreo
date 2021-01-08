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
import shutil

class xmlReadCreo:
	def __init__(self):
		self.__infoString = ""
		self.__errorString = ""
		self.__warningString = ""	
		self.refDesVals = []
		self.harnessNum = []
		self.wireLength = []
		self.alreadyProsessed = []
		self.prosessedSheets = []

#-----------------------------------------------------------------------------------------
# Create backup files of the schematic first
#
#-----------------------------------------------------------------------------------------						
	def backUpFile( self, fileToBackup ):
		self.fileToProcess = fileToBackup
		self.fileFirstBackup = fileToBackup+".bak"
		self.fileSecondBackup = fileToBackup+".bak2"
		self.returnVal = False		

		if os.path.exists( self.fileFirstBackup ):
			shutil.move( self.fileFirstBackup, self.fileSecondBackup)
			self.writeInfoStr("Moved first backup to second backup "+ self.fileSecondBackup + "\n")
			#print( "Moved first backup to second backup "+ self.fileSecondBackup, file=sys.stdout )
			
			
		if ( os.path.exists( self.fileToProcess )):
			try:
				os.rename( self.fileToProcess, self.fileFirstBackup )
				self.returnVal = True
			except OSError as error: 
				self.writeErrorStr(" Could not create Backupfile: " + self.fileFirstBackup + "\n")
		else:
			self.writeInfoStr( " File " + self.fileToProcess + " does not exist!\n" )

		return self.returnVal

#-----------------------------------------------------------------------------------------
# Write Kicad Schematic Sheet Data
#
#-----------------------------------------------------------------------------------------				
	def writeKicadSheet( self, sheetName ):
		for component in sheetName.components:
			for name, value in component.labels.items():
				if value[:1]=="W" or value[:3]=="CBL":
					refDes=value
					for field in component.fields:	
						for key in field.keys():
							# Get the component field "Length" and modify
							if field[key] == "\"Length\"":
								thisIsTheLengthParam = key
								try:
									myindex = self.refDesVals.index(refDes)
								except ValueError:
									self.writeErrorStr( "Refdes \""+refDes+"\" does not exist! Not routed yet?\n" )
									continue
								roundedWireLen = self.wireLength[myindex].split('.')[0]
								self.writeInfoStr("Name: " + "{0:<6}".format(refDes) + " Harness Name: " + "{0:<15}".format(self.harnessNum[myindex]) + " lenght: " +roundedWireLen + "\n")
								field['ref'] = "\""+roundedWireLen+"mm\""
							if field[key] == "\"Harness_name\"":
								thisIsTheHarnName = key						
								try:
									myindex = self.refDesVals.index(refDes)						
								except ValueError:
									self.writeErrorStr( "Refdes \""+refDes+"\" does not exist! Not routed yet?\n" )
									continue						
								harnessName = self.harnessNum[myindex]
								field['ref'] = "\""+harnessName+"\""
								
#		print( self.refDesVals )
#		print( self.wireLength )
#		print( self.harnessNum )



#-----------------------------------------------------------------------------------------
# Read data from Creo Schematic file (Created with Creo)
# and write the cable lengths and part numbers to Kicad Schematic file
# 
#
#-----------------------------------------------------------------------------------------				
	def backAnnotate( self, fileName ):
		self.creoSchXmlName = fileName +"_creoin.xml"
		self.kiCadOutputName = fileName +"_creo.sch"
		self.kiCadOriginalFile = fileName +".sch"		
			
		self.writeInfoStr( "Creo Back Annotation - Lengths and Harness Names\n" )								
		self.writeInfoStr( "------------------------------------------------\n" )								

		if( os.path.isfile(self.creoSchXmlName) ):
			self.writeInfoStr( "Creo Schematic Inputfile OK: " + self.creoSchXmlName + "\n" )								
		else:
			self.writeErrorStr( "Creo Schematic Inputfile NOT FOUND: " + self.creoSchXmlName + "\n" )
			self.writeInfoStr( "NOTE:You need to export Creo Schematic xml file with name: " + self.creoSchXmlName + "\n" )			
			self.writeInfoStr( "(Cabling -> Logical Data -> Export -> Creo Schematic)\n" )			
			return False
			
		if( os.path.isfile(self.kiCadOriginalFile) ):
			self.writeInfoStr( "Kicad Schematic Inputfile OK: " + self.kiCadOriginalFile + "\n" )										
		else:
			self.writeErrorStr( "Kicad Schematic Inputfile NOT FOUND: " + self.kiCadOriginalFile + "\n" )								
			return False
			
			
		creoXml = minidom.parse(self.creoSchXmlName)
		connections = creoXml.getElementsByTagName("CONNECTION")
		self.refDesVals = []
		self.harnessNum = []
		self.wireLength = []
		for connection in connections:
			wireName = connection.getAttribute("name")
			type = connection.getAttribute("type")
			varName = ""
			varValue = ""
			if wireName[:1] =="W" or type == "ASSEMBLY":
				self.refDesVals.append(wireName)
				parameters = connection.getElementsByTagName('PARAMETER')
				for param in parameters:
					varName = param.getAttribute('name')
					varValue = param.getAttribute('value')
					if( varName == "LENGTH" ):
						self.wireLength.append(varValue)
					if( varName == "HARNESS_NAME"):
						self.harnessNum.append(varValue)
					

		# Put lenghts to Kicad Schematic
		# Do not overwrite the original file
		self.writeInfoStr( "\nProcessing wires and cables:\n" )								
		self.writeInfoStr( "----------------------------\n" )								
		self.writeInfoStr( str(self.refDesVals) + "\n\n" )								

		myvariable = self.backUpFile( self.kiCadOriginalFile )
		kiCadSch = sch.Schematic( self.kiCadOriginalFile+".bak")
		self.writeKicadSheet( kiCadSch )
		kiCadSch.save( self.kiCadOriginalFile )

		# Process subsheets
		self.prosessedSheets = []
		for sheet in kiCadSch.sheets:			
			for field in sheet.fields:
				if( field['id'] =="F1" ):
					subSheetFilename = field['value'].replace('"', "")
					
					if( os.path.exists( subSheetFilename ) ):
						if( subSheetFilename in self.prosessedSheets ):
							self.writeWarningStr( "Child .sch already processed: " + subSheetFilename + "!\n" )							
							self.writeWarningStr( "NOTE: Reusing schematic shows the same wire\n" )							
							self.writeWarningStr( "lengths and partnames in all instances of the file.\n" )
							self.writeWarningStr( "Copy the .sch to a new name if you need\n" )								
							self.writeWarningStr( "to have unique names and wire lengths!\n" )								
						else:
							self.writeInfoStr( "\nProcessing child sheet " + subSheetFilename + "\n" )							
							myvariable = self.backUpFile( subSheetFilename )
							kicadChildSheet = sch.Schematic(subSheetFilename+".bak")
							self.writeKicadSheet( kicadChildSheet )
							kicadChildSheet.save( subSheetFilename )
							self.prosessedSheets.append(subSheetFilename)
					else:
						self.writeErrorStr( "File does not exist!: " + subSheetFilename + "\n" )																			
		return True
	
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
		
#-----------------------------------------------------------------------------------------
# If this is called Independently
#
# Create instance and call with parameters
#
#-----------------------------------------------------------------------------------------				
if __name__ == '__main__':      
	fileToProcess = sys.argv[1]    				# unpack 2 command line arguments  
	creoCablelengths = xmlReadCreo( )
	creoCablelengths.backAnnotate( fileToProcess )
	print("Info", file=sys.stdout)
	print( creoCablelengths.getInfoStr(), file=sys.stdout )

	print("Warnigns", file=sys.stdout)
	print( creoCablelengths.getWarningStr(), file=sys.stdout )

	print("Errors", file=sys.stderr)
	print( creoCablelengths.getErrorStr(), file=sys.stderr )
	
	
	
