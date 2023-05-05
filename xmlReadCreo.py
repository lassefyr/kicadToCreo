# -*- coding: utf-8 -*-
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
	
	Changes:
	2023.05.01	Kicad 7.0.2 hierarchical refdes issue patch. Not tested to work with all combinations.
	2022.03.01	Previous update broke V5 operation. Fixed.
	2022.01.01	added preliminary support for KicadV6
"""

from __future__ import print_function
from xml.dom import minidom
import sys
import sch
import os
import shutil
import math
#import sexpdata

class xmlReadCreo:
	def __init__(self):
		self.__infoString = ""
		self.__errorString = ""
		self.__warningString = ""	
		self.refDesVals = []
		self.harnessNum = []
		self.wireLength = []
		self.sheets = []
		self.alreadyProsessed = []
		self.prosessedSheets = []
		self.kiCadSch = object()

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
								roundedIntLen = math.ceil(float(self.wireLength[myindex]))
								roundedWireLen = str(roundedIntLen).split('.')[0] 				# Round up and no decimal places
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
# Find the Last refdes from the symbol -> instances-record
# Kicad has an uninvestigated way of storing the visible RefDes-values. This change was 
# added to Kicad 7.0.2. Without understanding why I just read the last refdes available...
# In current tests the the recursion count has been 9. Might get bigger 
# with deeper hierarchical designs.
#-----------------------------------------------------------------------------------------
#	recursiveCtr = 0
	lastRefDes = ""
	def find_RefDes( self, listItem ):
		from sexpdata import Symbol, car, cdr
		#self.recursiveCtr+=1
		for i, j in  enumerate(listItem):		
			if ( not hasattr(j, "__getitem__") ):
				return				
			elif ( isinstance( car(j), Symbol ) and ( car(j) != Symbol("reference")) ):		
				if( hasattr(j, "__getitem__") ):
					self.find_RefDes( j )
			elif( isinstance( car(j), Symbol) and ( car(j)== Symbol("reference")) ):
				self.lastRefDes = cdr(j)[0]				
				
#-----------------------------------------------------------------------------------------
# Write Kicad V6 Schematic Sheet Data
#
#-----------------------------------------------------------------------------------------				
	def writeKicadSch_v6( self ):
		from sexpdata import Symbol, car, cdr
		for i, x in enumerate(self.kiCadSch):
			if ( car(x) == Symbol('symbol') ): 
				refDes = ""
				for j, y in enumerate(x):		
				#---------------------------------------------------
				# Check if this item is a cable or a wire. If not then continue
				#---------------------------------------------------
					if ( (car(y) == Symbol('property')) and  ( cdr(y)[0]== "Reference" )): 
						if( (cdr(y)[1][:1] == 'W') or (cdr(y)[1][:3]=="CBL")):							
							refDes = cdr(y)[1]
							# Find instance reference designator
							for d, z in  enumerate(x):
								if ( car(z) == Symbol('instances') ):
									#self.recursiveCtr=0
									self.lastRefDes = ""
									self.find_RefDes( z )
									#print( "FINAL REFDES = "+self.lastRefDes)
									#print( "recursionCount = "+ str(self.recursiveCtr))
									if(self.lastRefDes):
										refDes = self.lastRefDes
						else:
							continue	
					
				#---------------------------------------------------
				# Process the lengths and the Part Numbers
				#---------------------------------------------------
				# Update the Harness Name String if it exists
					if ( car(y) == Symbol('property') ):
						if( cdr(y)[0].lower() == "harness_name" ):		#note - lower case
							try:
								myindex = self.refDesVals.index(refDes)						
							except ValueError:
								self.writeErrorStr( "Refdes \""+refDes+"\" does not exist! Not routed yet?\n" )
								continue						
							harnessName = self.harnessNum[myindex]
							y[2] = harnessName										
					#---------------------------------------------------
					# Update the Harness Length String if it exists
						if( cdr(y)[0].lower() == "length" ):
							try:
								myindex = self.refDesVals.index(refDes)
							except ValueError:
								self.writeErrorStr( "Refdes \""+refDes+"\" does not exist! Not routed yet?\n" )
								continue
							roundedIntLen = math.ceil(float(self.wireLength[myindex]))
							roundedWireLen = str(roundedIntLen).split('.')[0] 				# Round up and no decimal places
							self.writeInfoStr( "Name: " + "{0:<6}".format(refDes) + " Harness Name: " + "{0:<15}".format(self.harnessNum[myindex]) + " lenght: " +roundedWireLen + "\n" )
							y[2] = (roundedWireLen+"mm")
	
#-----------------------------------------------------------------------------------------
# Read data from Creo xml and store the read lengths, part numbers, and refdes values.
#
#-----------------------------------------------------------------------------------------
	def readCreoPartNumsAndLengths( self, fileName ):
		self.creoSchXmlName = os.path.splitext(fileName)[0] +"_creoin.xml"
			
		self.writeInfoStr( "Creo Back Annotation - Lengths and Harness Names\n" )								
		self.writeInfoStr( "------------------------------------------------\n" )								

		if( os.path.isfile(self.creoSchXmlName) ):
			self.writeInfoStr( "Creo Schematic Xml-file OK: " + self.creoSchXmlName + "\n" )								
		else:
			self.writeErrorStr( "Creo Schematic Inputfile NOT FOUND: " + self.creoSchXmlName + "\n" )
			self.writeInfoStr( "NOTE:You need to export Creo Schematic xml file with name: " + self.creoSchXmlName + "\n" )			
			self.writeInfoStr( "(Cabling -> Logical Data -> Export -> Creo Schematic)\n" )			
			return False
									
		creoXml = minidom.parse( self.creoSchXmlName )
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


#-----------------------------------------------------------------------------------------
# Read existing sheetnames in the design
#
#-----------------------------------------------------------------------------------------
	def readCreoSheetNames( self, fileName ):
		self.creoSchXmlName = fileName +".xml"
		
		creoXml = minidom.parse( self.creoSchXmlName )		
		sheetNames = creoXml.getElementsByTagName("sheet")
		
		self.sheets = []
		for mysheet in sheetNames:
			x = mysheet.getElementsByTagName("source")[0]
			y =x.childNodes[0];		
			self.sheets.append( y.nodeValue )
		
		del creoXml


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
# Read data from Creo Schematic file (Created with Creo)
# and write the cable lengths and part numbers to Kicad V6 Schematic file
# 
#
#-----------------------------------------------------------------------------------------
	def backAnnotateV6( self, fileName ):
		from sexpdata import loads, dumps
		
		# Put lenghts to Kicad Schematic
		# Do not overwrite the original file
		self.writeInfoStr( "\nProcessing wires and cables:\n" )								
		self.writeInfoStr( "----------------------------\n" )								
		self.writeInfoStr( str(self.refDesVals) + "\n\n" )								
		

		self.prosessedSheets = []	
		currentDirectory = os.path.dirname( fileName )
		for myfilename in self.sheets:
			#------------------------------------------------------------------
			# Error Cheking
			myfilename = os.path.join( currentDirectory, myfilename )
			if( os.path.exists( myfilename ) ):
				if( myfilename in self.prosessedSheets ):
					self.writeWarningStr( "Child .sch already processed: " + myfilename + "!\n" )
					self.writeWarningStr( "NOTE: Reusing schematic shows the same wire\n" )							
					self.writeWarningStr( "lengths and partnames in all instances of the file.\n" )
					self.writeWarningStr( "Copy the .sch to a new name if you need\n" )								
					self.writeWarningStr( "to have unique names and wire lengths!\n" )
					continue
				elif ( self.backUpFile( myfilename ) ):
					self.writeInfoStr( "\nBacking up " + myfilename + " OK\n" )
				else:
					self.writeErrorStr( "\nBacking up " + myfilename + " FAILED\n" )
					continue
			#------------------------------------------------------------------
			# Process sheet for partnumbers and lengths								
				try:
					f = open((myfilename+".bak"),"r")
					self.line = f.read()
				except:
					self.writeErrorStr( "Could not read file: " + myfilename +".bak !\n" )
					continue
				finally:
					self.kiCadSch = loads( self.line )
					self.writeKicadSch_v6( )
					f.close( )					
				try:
					f = open( myfilename, "w" )
					f.write(dumps( self.kiCadSch ))
				except:
					self.writeErrorStr( "Could not write file: " + myfilename + "!\n" )
				finally:
					self.writeInfoStr( "Updated file: " + myfilename + " succesfully.\n" )
					f.close( )
				self.prosessedSheets.append( myfilename )
				
			else:
				self.writeErrorStr( "File does not exist!: " + myfilename + "\n" )
		return True

#-----------------------------------------------------------------------------------------
# Read the correct filename from the .xml file
#
#-----------------------------------------------------------------------------------------				
	def getSourceFilenameFromXml( self, xmlFileName ):
		tmpObject = minidom.parse(xmlFileName)
		currentFileName = tmpObject.getElementsByTagName("source")
		del tmpObject
		return( currentFileName[0].firstChild.nodeValue )
		
		
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
	
	# Split the file extension away if it exists. This comes from command line
	# fileNameToProcess = os.path.splitext(fileToProcess)[0]

	# Initialize the function instance
	creoCablelengths = xmlReadCreo( )
	
	# Get the filename from the xml-File
	tempFileName = creoCablelengths.getSourceFilenameFromXml( fileToProcess )
	fileNameToProcess = os.path.splitext(tempFileName)[0]
	fileExtension = os.path.splitext(tempFileName)[1]
	
	if( fileExtension == ".sch" ):
		creoCablelengths.writeInfoStr( "\nProsess Kicad V5 file.\n")
		creoCablelengths.readCreoPartNumsAndLengths( fileToProcess )
		creoCablelengths.readCreoSheetNames( fileNameToProcess )
		creoCablelengths.backAnnotate( fileNameToProcess )
	elif( fileExtension == ".kicad_sch" ):
		creoCablelengths.writeInfoStr( "\nProsess Kicad V6 file.\n")
		creoCablelengths.readCreoPartNumsAndLengths( fileToProcess )
		creoCablelengths.readCreoSheetNames( fileNameToProcess )
		creoCablelengths.backAnnotateV6( fileNameToProcess )	
	else:
		creoCablelengths.writeInfoStr( "\nNo Valid Filename found " + fileToProcess + "\n" )
	
	print("Info", file=sys.stdout)
	print( creoCablelengths.getInfoStr(), file=sys.stdout )

	print("Warnigns", file=sys.stdout)
	print( creoCablelengths.getWarningStr(), file=sys.stdout )

	print("Errors", file=sys.stderr)
	print( creoCablelengths.getErrorStr(), file=sys.stderr )
	print( "Please Reload the Kicad Schematic if Operation was Successful", file=sys.stdout )
	