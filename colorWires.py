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
    Run from Kicad eeschema with parameters "%I" 0.5
		"%I" is the generated xml file
		0.5 is the requested line width  (value less than 1)
		If the float parameter is omitted then the line width will be 0.3
	
	Changes:
	2023.02.12  Fixed for v.7.0. Added Color list for wires if they don't already exist
	
"""

from __future__ import print_function
from xml.dom import minidom
import sys
import sch
import os
import shutil
import math
#import sexpdata

#-----------------------------------------------------------------------------------------
# Colors dictionary:
# All colors that exists in wires and cables must be found here
# Pleas add color to this table if it does not exist.
# Values are (RED, GREEN, BLUE)
#-----------------------------------------------------------------------------------------
colors = {
	"black": (0, 0, 0),
	"brown": (0x99, 0x66, 0x33),
	"red": (0xff, 0, 0),
	"orange": (0xff, 0x99, 0),
	"yellow": (0xff, 0xff, 0),
	"green": (0, 255, 0),
	"blue": (0, 0, 255),
	"violet": (255, 0, 255),
	"grey": (0xcc, 0xcc, 0xcc),
	"gray": (0xcc, 0xcc, 0xcc),
	"white": (0xdd, 0xdd, 0xdd),
	"gold": (0, 0, 0),
	"silver": (255, 255, 255), 
	"ral4002": (141, 60, 75),
	"ral8004": (140, 86, 73)
}

#-----------------------------------------------------------------------------------------
# cblWireData
# A list of these classes is created for each cable and wire on the schematic
# 
#-----------------------------------------------------------------------------------------
class cblWireData:
	def __init__(self, refDes ):
		self.wireOrCbl = refDes
		self.symbolName = ""
		self.mirror = ""
		self.numWires = 0
		self.colors = []
		self.xcoord = 0
		self.ycoord = 0
		self.rotation = 0
		self.pinxcoord = []
		self.pinycoord = []
		self.pinIndex = []

	def getWireOrCbl( self ):
		return( self.wireOrCbl )
	
	def getX( self ):
		return( self.xcoord )

	def getY( self ):
		return( self.ycoord )

	def getAngle( self ):
		return( self.rotation )
		
	def getColors( self ):
		return( self.colors )
		
	def getSymName( self ):
		return( self.symbolName )
		
	def getPinX( self ):
		return( self.pinxcoord )

	def getPinY( self ):
		return( self.pinycoord )
		
	def getPinIndex( self ):
		return( self.pinIndex )
	
	def getNumOfPins( self ):	
		return( len(self.pinycoord) )					# How many pin Y coordinates = how many pins (same as num of x coordinates)
		
	def getColor ( self, index ):
		if( self.wireOrCbl[:1] == "W" ):
			return self.colors[0]
		else:		
			myInd = self.pinIndex[ index ]+1
			myInd = int(myInd/2)
			if( len(self.colors) <= myInd ):
				self.writeWarningStr( "getColor Index out of Range! Return \"black\" Color!\n" )
				return("black")
			else:
				return self.colors[myInd]
			
	def getPinCoordinate( self, pinNum ):
		if(pinNum < len(self.pinycoord)):
			if( self.rotation == 90 ):
				if( self.mirror == "x" ):
					myx = self.xcoord - self.pinycoord[ pinNum ]
					myy = self.ycoord + self.pinxcoord[ pinNum ]
				else:
					myx = self.xcoord - self.pinycoord[ pinNum ]
					myy = self.ycoord - self.pinxcoord[ pinNum ]
				
			elif( self.rotation == 180 ):
				myx = self.xcoord - self.pinxcoord[ pinNum ]
				myy = self.ycoord + self.pinycoord[ pinNum ]
				
			elif( self.rotation == 270 ):
				if( self.mirror == "x" ):
					myx = self.xcoord + self.pinycoord[ pinNum ]
					myy = self.ycoord - self.pinxcoord[ pinNum ]
				else:
					myx = self.xcoord + self.pinycoord[ pinNum ]
					myy = self.ycoord + self.pinxcoord[ pinNum ]
			else:
				if( self.mirror == "x" ):					
					myx = self.xcoord + self.pinxcoord[ pinNum ]
					myy = self.ycoord + self.pinycoord[ pinNum ]
				elif( self.mirror == "y" ):
					myx = self.xcoord - self.pinxcoord[ pinNum ]
					myy = self.ycoord - self.pinycoord[ pinNum ]
				else:
					myx = self.xcoord + self.pinxcoord[ pinNum ]
					myy = self.ycoord - self.pinycoord[ pinNum ]
			
			myxFloat = round(myx, 2)
			myyFloat = round(myy, 2)
			
			#print (myxStr + "   " + myyStr)		
			return(myxFloat, myyFloat)
		else:
			return(0, 0)
	
	def getMirrorVal( self ):
		return( self.mirror )
		
	def setMirrorVal( self, myMirror ):
		self.mirror = myMirror
		
	def setNumWires( self, numOfWires ):
		self.numWires = numOfWires

	def setSymName( self, symName ):
		self.symbolName = symName

	def setColorName( self, color, index ):
		if( self.wireOrCbl[:1] == "W" ):
			self.colors.append(color)
		else:
			try:
				self.colors[ index ] = color
			except IndexError:
				for _ in range(index - len(self.colors) + 1):
					self.colors.append(None)
					self.colors[index] = color
		
	def setXY( self, xCoord, yCoord, compAngle ):
		self.xcoord = xCoord
		self.ycoord = yCoord
		self.rotation = compAngle

	def setPinXY( self, xCoord, yCoord, Direction ):
		self.pinxcoord.append(xCoord)
		self.pinycoord.append(yCoord)
		self.pinIndex.append(Direction)


#-----------------------------------------------------------------------------------------
# class setWireColor:
# Sets the colors on the schematic
# Uses the same basic construcs as the backannotation uses.
#-----------------------------------------------------------------------------------------
class setWireColor:
	def __init__(self, wireWidth = 0.3):
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
		self.modifiedKiCadSch = object()
		self.myUUids = []
		self.useThisWidth = wireWidth
		

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
# Colorize Kicad V6 Schematic Wires 
#  - Read the color from the wire or cable symbol
#  - Colorize the wires accordingly
#-----------------------------------------------------------------------------------------
	def writeKicadSch_v6( self ):
		from sexpdata import Symbol, car, cdr		
		thisLibPart = ""		
		xcoord = 0
		ycoodr = 0
		rotate = 0

		myWires = []
		self.myUUids = []
		
		for i, x in enumerate(self.kiCadSch):
			if ( car(x) == Symbol('symbol') ):
				refDes = ""
				thisMirror = ""
				for j, y in enumerate(x):
				#---------------------------------------------------
				# Check if this item is a cable or a wire. If not then continue
				#---------------------------------------------------
					if ( car(y) == Symbol('lib_id') ):
						thisLibPart = cdr(y)[0]						
					if (car(y) == Symbol('mirror')):
						thisMirror = str(cdr(y)[0])
					if ( car(y) == Symbol('at') ):
						xcoord = (cdr(y)[0])
						myfloat = cdr(y)[0]
						ycoord = (cdr(y)[1])
						rotate = int( cdr(y)[2] )
				#---------------------------------------------------
				# Check if this item is a cable or a wire. If not then continue
				#---------------------------------------------------
					if ( (car(y) == Symbol('property')) and  ( cdr(y)[0]== "Reference" )):
						if( (cdr(y)[1][:1] == 'W') or (cdr(y)[1][:3]=="CBL")):
							refDes = cdr(y)[1]
							myWires.append( cblWireData( refDes ) )
							myWires[-1].setSymName( thisLibPart )
							myWires[-1].setXY( xcoord, ycoord, rotate )
							myWires[-1].setMirrorVal( thisMirror )
						else:
							continue

				#---------------------------------------------------
				# Process the lengths and the Part Numbers
				#---------------------------------------------------
				# Update the Harness Name String if it exists
					if ( car(y) == Symbol('property') ):
						if( cdr(y)[0].lower() == "color" ):		#note - lower case
							myWires[-1].setColorName(y[2], 0)
															
		#----------------------------------------------------------------------
		# Set library compontent values
		# Pin Offsets and Colors for cables ...
		#----------------------------------------------------------------------
		symbolName = ""
		for i, x in enumerate(self.kiCadSch):
			if ( car(x) == Symbol('lib_symbols') ):
				for j, y in enumerate(x):
					if ( car(y) == Symbol('symbol') ):
						symbolName = cdr(y)[0]
						cableOrWire = ""	
						for z, b in enumerate(y):
							if ( (car(b) == Symbol('property')) and cdr(b)[0]==('Reference') ):
								if( cdr(b)[1] == "W" or  cdr(b)[1] == "CBL" ):
									cableOrWire = cdr(b)[1]
								else:
									continue

							if ( (car(b) == Symbol('property')) and ((cdr(b)[0].lower())[:5])==('color') ):
								for i in myWires:
									if i.getSymName() in symbolName:
										if ( len(cdr(b)[0]) != 5 ):									
											i.setColorName( cdr(b)[1], int((cdr(b)[0][5:]) ))
								
							if( cableOrWire == "W"  or  cableOrWire == "CBL" ):
								if ( car(b) == Symbol('symbol') ):
									for za, zb in enumerate(b):
										if ( car(zb) == Symbol("pin") ):
											for i in myWires:
												if i.getSymName() in symbolName:
													i.setPinXY( (cdr(zb)[2][1]), (cdr(zb)[2][2]), int(cdr(zb)[5][1]))
		'''
		for i in myWires:
			print( i.getWireOrCbl() +" x= " + str(i.getX()) + " Y = " + str(i.getY()),end = "" )
			print ( i.getPinX() ,end = "")
			print ( i.getPinY() ,end = "")
			print ( i.getPinIndex() ,end = "")
			print ( i.getColors(),end = "")
			print ( ", Mirror = "+i.getMirrorVal(),end = "")
			print ("  Rot Angle = "+str(i.getAngle()))
		'''
		
		self.myUUids = []
		for b in myWires:
			numOfPins = b.getNumOfPins( )			
			if( numOfPins < 2 ):
				self.writeWarningStr( "Too Few Pins! Min = 2 pins for wires!\n" )
				continue
			for myPins in range(numOfPins):
				currentColor = 	(b.getColor(myPins).split(',')[0])			# some pins may have awg etc information
				# print("Current color = " + currentColor)
				
				nextCoordinates = []
				nextCoordinates.append((b.getPinCoordinate(myPins)))								
				self.setWireFollowColor(nextCoordinates, currentColor)

#-----------------------------------------------------------------------------------------
# def appendWireColorToSchematic( self ):
#
#	Kicad 7 omits the wire color fields on wires.
#	This creates the wirecolor fields on the file...
#
#	listofstuff = ['Joe', 'Bob', 'Mary']
#	dct = {name: classthing(name) for name in listofstuff}			
#-----------------------------------------------------------------------------------------		
	def appendWireColorToSchematic( self ):
		from sexpdata import Symbol, car, cdr
			
		mylist = []
		templist = []
		for i, x in enumerate(self.kiCadSch):
			if ( car(x) == Symbol('wire') ):
				#mylist.append(car(x))
				for j, y in enumerate(x):	
					if ( car(y) == Symbol('stroke') ):
						if( len((cdr(y))) == 2 ):								# Append if doesn't exist. Don't do anything if already present
							y.append([Symbol("color"), 0, 0, 0, 1])							
				mylist.append(x)
			else:
				mylist.append(x)
		#print(mylist)
		#print("-----------------------------")
		#print(self.kiCadSch)
		self.kiCadSch = mylist
		'''
		try:
			f = open( "perse.kicad_sch", "w" )
			f.write(dumps( mylist ))
		except:
			self.writeErrorStr( "Could not write file: " + os.path.splitext(myfilename)[0]+"_col.kicad_sch" + "!\n" )
		finally:
			self.writeInfoStr( "Writing file: succesfully.\n" )
			f.close( )
		'''

#-----------------------------------------------------------------------------------------
# def setWireFollowColor ( self, xyTuples, wireColor ):
#
#	Color wires according to wireColor
#-----------------------------------------------------------------------------------------
	def setWireFollowColor ( self, xyTuples, wireColor ):
		from sexpdata import Symbol, car, cdr
	#  list_name.pop(index) (if no index then the last is pop).			
		nextCoordinates = []
		firstWireFromCbl = True
		
		while xyTuples: 		# while there are coordinates on the list				
			myx, myy = xyTuples.pop( )
			
			for i, x in enumerate(self.kiCadSch):
				
				tempX = float(0)
				tempy = float(0)
				tempred = 0
				tempgreen = 0
				tempblue = 0
				wireThickness = self.useThisWidth
				tempSymbolList = []
				
				if ( car(x) == Symbol('wire') ):
					matchFlag = False
					#print(x)
					#print("-------------------")
					for j, y in enumerate(x):	
						if ( car(y) == Symbol('pts') ):
							x1 = cdr(y)[0][1]
							y1 = cdr(y)[0][2]
							x2 = cdr(y)[1][1]
							y2 = cdr(y)[1][2]
							
							if( math.isclose(myx, x1, abs_tol = 0.01) and  math.isclose(myy, y1, abs_tol = 0.01) ): #if( myx == x1 and myy == y1 ):							
								matchFlag = True
								tempX = x2
								tempY = y2
							if( math.isclose(myx, x2, abs_tol = 0.01) and  math.isclose(myy, y2, abs_tol = 0.01) ): #if( myx == x2 and myy == y2 ):							
								matchFlag = True
								tempX = x1
								tempY = y1	
							continue													
						
						if( car(y) == Symbol("stroke") and matchFlag):
							# Save this position to be changed later if necessary							
							# (stroke (width 0.127) (type solid) (color 194 0 0 1)) Hex #C2 00 00 FF, R G B, 0xff is opacity = 1 (value between 0-1)							
							tempSymbolList = cdr(y)
							if wireColor.lower() in colors.keys():
								tempred, tempgreen, tempblue = colors.get(wireColor.lower())
							else:
								self.writeErrorStr("Color "+ wireColor + " Not in Dictionary. Using Default Color" + "\n")
								tempred, tempgreen, tempblue = 45, 77, 88								
							continue
							
						if( car(y) == Symbol("uuid") and matchFlag):
							matchFlag = False							
							tempUUid = str(cdr(y)[0])
							
							if ((firstWireFromCbl) or (not tempUUid in self.myUUids) ):
								firstWireFromCbl = False
								self.myUUids.append(tempUUid)								
								xyTuples.append((tempX,tempY))															
								tempSymbolList[0][1] = wireThickness								
								tempSymbolList[2][1] = tempred
								tempSymbolList[2][2] = tempgreen
								tempSymbolList[2][3] = tempblue
								tempSymbolList[2][4] = 1										
							
							continue
						
#-----------------------------------------------------------------------------------------
# Read existing sheetnames in the design
#
#-----------------------------------------------------------------------------------------
	def readCreoSheetNames( self, fileName ):
		self.creoSchXmlName = fileName +".xml"

		if( not os.path.isfile(self.creoSchXmlName) ):
			sys.exit("error: xml file not found!")
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
# and write the cable lengths and part numbers to Kicad V6 Schematic file
#
#
#-----------------------------------------------------------------------------------------
	def colorAllWires( self, fileName ):
		from sexpdata import loads, dumps

		# Put lenghts to Kicad Schematic
		# Do not overwrite the original file
		self.writeInfoStr( "\nColorizing wires and cables:\n" )
		self.writeInfoStr( "----------------------------\n" )		

		self.prosessedSheets = []
		currentDirectory = os.path.dirname( fileName )
		
		#print(self.sheets)
		for myfilename in self.sheets:
			#------------------------------------------------------------------
			# Error Checking
			myfilename = os.path.join( currentDirectory, myfilename )
			if( os.path.exists( myfilename ) ):
				if( myfilename in self.prosessedSheets ):
					self.writeWarningStr( "Child .sch already processed: " + myfilename + "!\n" )
					self.writeWarningStr( "NOTE: Reusing schematic shows the same wire\n" )
					self.writeWarningStr( "lengths and partnames in all instances of the file.\n" )
					self.writeWarningStr( "Copy the .sch to a new name if you need\n" )
					self.writeWarningStr( "to have unique names and wire lengths!\n" )
					continue

			#------------------------------------------------------------------
			# Colorize sheets. Rename the sheet with new name (for now)
				self.line = ""

				try:					
					f = open(myfilename,"r")
					self.line = f.read()
				except:
					self.writeErrorStr( "Could not read file: " + myfilename +".kicad_sch !\n" )
					continue
				finally:
					self.kiCadSch = loads( self.line )
					self.appendWireColorToSchematic( )										# Overwrites the self.kiCadSch
					self.writeKicadSch_v6( )					
					f.close( )
					#sys.exit("test exit")
				
				try:
					f = open( os.path.splitext(myfilename)[0]+"_col.kicad_sch", "w" )
					f.write(dumps( self.kiCadSch ) )										# Pretty_print=True 
				except:
					self.writeErrorStr( "Could not write file: " + os.path.splitext(myfilename)[0]+"_col.kicad_sch" + "!\n" )
				finally:
					self.writeInfoStr( "Writing file: " + os.path.splitext(myfilename)[0]+"_col.kicad_sch" + " succesfully.\n" )
					f.close( )
				
				self.writeInfoStr( "Processed file: " + myfilename + " succesfully.\n" )
				self.prosessedSheets.append( myfilename )

			else:
				self.writeErrorStr( "File does not exist!: " + myfilename + "\n" )
		return True

#-----------------------------------------------------------------------------------------
# Read the correct filename from the .xml file
#
#-----------------------------------------------------------------------------------------
	def getSourceFilenameFromXml( self, xmlFileName ):
		if( not os.path.isfile(xmlFileName) ):
			sys.exit("error: xml file not found!")	
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

	wireWidth = float(0.3)
	
	n = len(sys.argv)
	
	if( n == 2 ):
		print("Using default Wire Width = 0.3 for all wires!")
	elif( n == 3 ):
		try:
			wireWidth = float(sys.argv[2])
		except ValueError:
			print( "Second argument is not a float number" )
			sys.exit("Error")
			
		if( wireWidth > 1):
			wireWidth = 1
			print( "Using Max Width = 1.0" )
	else:
		sys.exit( "Too Few Parameters" )
	
	#sys.exit(0)
	fileToProcess = sys.argv[1]    					# unpack 2 command line arguments

	# Split the file extension away if it exists. This comes from command line
	# fileNameToProcess = os.path.splitext(fileToProcess)[0]

	# Initialize the function instance
	wireColors = setWireColor( wireWidth )

	# Get the filename from the xml-File
	tempFileName = wireColors.getSourceFilenameFromXml( fileToProcess )
	fileNameToProcess = os.path.splitext(tempFileName)[0]
	fileExtension = os.path.splitext(tempFileName)[1]

	if( fileExtension == ".kicad_sch" ):
		wireColors.writeInfoStr( "\nProcess Kicad >=V6 file.\n")
		wireColors.readCreoSheetNames( fileNameToProcess )
		wireColors.colorAllWires( fileNameToProcess )
	else:
		wireColors.writeInfoStr( "\nNo Valid Filename found " + fileToProcess + "\n" )

	print("Info", file=sys.stdout)
	print( wireColors.getInfoStr(), file=sys.stdout )

	print("Warnigns?", file=sys.stdout)
	print( wireColors.getWarningStr(), file=sys.stdout )

	print("Errors?", file=sys.stderr)
	print( wireColors.getErrorStr(), file=sys.stderr )
	basename_noext = os.path.basename(tempFileName).split('.', 1)[0]
	print( "Please load the Kicad Schematic named "+ basename_noext+"_col.kicad_sch if Operation was Successful", file=sys.stdout )	

