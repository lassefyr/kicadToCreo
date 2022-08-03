# -*- coding: utf-8 -*-
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

# Import the KiCad python helper module
import kicad_netlist_reader
import sys
import os
import xmlWriteCompData
import xmlWriteSpools
import xmlWriteConnections

import wx	# 2022_08_03 using wx now. Seems to work in both kicad versions 5 and 6
	
import logging
import threading
import textwrap

#------------------------------------------------------------------------------
# 	Text Handler class for the wx Interface
#	class TextHandler(logging.Handler):
#	Scrolls text with different text colors
#------------------------------------------------------------------------------     
class TextHandler(logging.Handler):
	"""This class allows you to log to a wx Text or ScrolledText widget"""
	def __init__(self, text):
		# run the regular Handler __init__
		logging.Handler.__init__(self)
		# Store a reference to the Text it will log to
		self.text = text
		
	# Set different Background colors for error and warning messages.
	# You can set the foreground and background color to what ever you like here
	def emit(self, record):
		msg = self.format(record)
		
		if(record.levelname == "ERROR"):
			self.text.SetDefaultStyle(wx.TextAttr(wx.RED,  wx.WHITE))					
		elif(record.levelname == "WARNING"):
			self.text.SetDefaultStyle(wx.TextAttr(wx.GREEN,  wx.WHITE))					
		else:
			self.text.SetDefaultStyle(wx.TextAttr(wx.BLACK,  wx.WHITE))				
		
		# Wrap long lines. You can adjust the line length here
		for line in msg.split('\n'):
			if len(line) >= 80: 
				for splitline in textwrap.wrap(line, width=80):
					self.text.AppendText( splitline+"\n" )
			else:
				self.text.AppendText( line+"\n" )

#------------------------------------------------------------------------------
# 	Check parameters
#------------------------------------------------------------------------------   			
if len(sys.argv) < 3:
    print("Usage ", __file__, "<netlist.xml> <output file> <optional dummy for wx interface>", file=sys.stderr)
    sys.exit(1)

# Check whether we want console or wx window app
wantUiWin = False
if len(sys.argv) == 4:
	wantUiWin = True

# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop

if( os.path.isfile( sys.argv[1] ) ):
	netlist = kicad_netlist_reader.netlist(sys.argv[1])
	inputFileName = sys.argv[1]
	creoLogicalFileName = sys.argv[2]+"_creo.xml"
else:
	print("File not Found: " + sys.argv[1] + " !\nExit Script!", file=sys.stderr)
	sys.exit(1)
	

#------------------------------------------------------------------------------
#	Generate a YAML style netlist
#	components = netlist.getInterestingComponents()
#	This overwrites the old file and starts a new.
#------------------------------------------------------------------------------       
def writeFileHeader( outputFileName ):
	actualFileOpened = False
	if len(outputFileName) > 2:
		try:
			if sys.version_info.major < 3:		
				fout = open(outputFileName, "w")
			else:
				fout = open(outputFileName, "w", encoding='utf-8')
			actualFileOpened = True
		except IOError:
			e = "Can't open output file for writing: " + outputFileName
			print( __file__, ":", e, sys.stderr )
			fout = sys.stdout
	else:
		fout = sys.stdout

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
	
	# Individual functions will open the outputfile as needed	
	if actualFileOpened == True:
		fout.close()

#------------------------------------------------------------------------------
#	Append rsData tag to file END...
#------------------------------------------------------------------------------
def writeFileEnd( outputFileName ):
	actualFileOpened = False
	if len(outputFileName) > 2:
		try:
			if sys.version_info.major < 3:		
				fout = open(outputFileName, "a")
			else:
				fout = open(outputFileName, "a", encoding='utf-8')				
			actualFileOpened = True
		except IOError:
			e = "Can't open output file for writing: " + outputFileName
			print( __file__, ":", e, sys.stderr )
			fout = sys.stdout
	else:
		fout = sys.stdout

	print("</rsData>", file = fout)
	
	# Individual functions will open the outputfile as needed	
	if actualFileOpened == True:
		fout.close( )
	import codecs
	try:
		f = codecs.open(outputFileName, encoding='utf-8', errors='strict')
		for line in f:
			pass
		if(wantUiWin):
			logger.info( "Valid utf-8" )
		else:
			print("Valid utf-8", file = sys.stdout)
		f.close()
	except UnicodeDecodeError:
		f.close()			
		if(wantUiWin):
			logger.error( "Invalid utf-8" )			
		else:
			print("invalid utf-8", file = sys.stderr)
		
#------------------------------------------------------------------------------
#	Progress Bar for the wx interface
#	Todo:
#		- use the filename from the "Output Filename" - Dialog
#		- allow filename to be changed.
#		- check that the filename ends as "_crea.xml"
#------------------------------------------------------------------------------
def bar( event ):
	import time 
	
	progress.SetValue( 0 )
	progress.Show()
	# Clear Logger buffer. You must first set the state to normal before clearing.	
	st.Clear( )
	lbl_progress.SetLabel("Running...")
	
	logger.info('Started ' + time.strftime('%H:%M:%S'))
	
	outPutFName = fNameEntry.GetValue( )
	if( os.path.isfile( outPutFName ) ):
		logger.info("\nNI: Output Filename Exists: Overwriting")
	else:
		logger.info("\nNI: Output Filename does not Exist: Creating")
		
	if( outPutFName.lower().endswith(('_creo.xml')) ):
		logger.info("NI: Correct filename: Ends with \"_creo.xml\"\n")
	else:
		logger.info("NI: Invalid filename: \""+outPutFName+"\" Ignoring!\n")
	
	if( not mkCreoBtn.GetValue( ) ):
		logger.info("NI: Creo xml box not checked. Ignored!\n")	
	
	writeFileHeader( creoLogicalFileName )
	
	progress.SetValue( 30 )
	logger.info('Writing component Information')
	# Write Components ------------------------------------
	components = xmlWriteCompData.xmlWriteCompData()
	components.writeCompData(netlist,creoLogicalFileName)
	# Get connection warnings and errors
	logger.info( components.getInfoStr() )
	logger.warning( components.getWarningStr() )
	logger.error( components.getErrorStr() )
	
	wx.Yield()
	
	progress.SetValue( 66 )
	logger.info('\nWriting Spools')
	# Write Spools ----------------------------------------
	spools = xmlWriteSpools.xmlWriteSpools()
	spools.writeSpoolData(netlist,creoLogicalFileName)
	# Get Spool warnings and errors
	logger.warning( spools.getWarningStr() )
	logger.error( spools.getErrorStr())
	logger.info( 'Spools Found and Created...' )
	logger.info( spools.printCblSpoolNames() )	
	
	wx.Yield()

	progress.SetValue( 95 )
	logger.info('\nWriting Connections')
	# Write Connections -----------------------------------
	connections = xmlWriteConnections.xmlWriteConnections( spools )
	connections.writeConnections( netlist,creoLogicalFileName )
	# Get Connection warnings and errors
	logger.warning( connections.getWarningStr() )
	logger.error( connections.getErrorStr() )

	wx.Yield()
	
	progress.SetValue( 100 )
	writeFileEnd( creoLogicalFileName )	
	lbl_progress.SetLabel("Done!")
	
#------------------------------------------------------------------------------
#	Back Annotation button
#		Reads the Creo logical file and updates Lengths and Part names to Schematic.
#	Todo:
#		- Does not nesessarily work at this time.
#		- More Checks needed
#------------------------------------------------------------------------------
def BackAnn( event ):
	import time 
	
	import xmlReadCreo
	
	# Clear Logger buffer. You must first set the state to normal before clearing.	
	st.Clear( )
	lbl_progress.SetLabel("Running...")
	
	logger.info('Started ' + time.strftime('%H:%M:%S'))
	
	creoLogicalFileName = os.path.splitext(inputFileName)[0]
	if( os.path.isfile( ( creoLogicalFileName+"_creoin.xml" )) ):
		logger.info("\nNI: Logical file from Creo Exists. Proceeding")
	else:
		logger.error("\nERROR: Creo Logical File Does Not Exist: Cancelling!")
		lbl_progress.SetLabel("Error!")
		return
	
	
	# Split the file extension away if it exists
	fNameWoExtension = os.path.splitext(inputFileName)[0]
	creoCablelengths = xmlReadCreo.xmlReadCreo( )
	creoCablelengths.backAnnotate( fNameWoExtension )
	
	logger.info( "Back Annotate Info" )
	logger.info( creoCablelengths.getInfoStr() )	
	
	logger.warning( "Back Annotate Warnigns" )
	logger.warning( creoCablelengths.getWarningStr() )
	
	logger.error( "Back Annotate Errors" )
	logger.error( creoCablelengths.getErrorStr())
	logger.info( "Please Reload the Kicad Schematic" )	
	lbl_progress.SetLabel("Done!")
	

#------------------------------------------------------------------------------
# Create the tKinter window if needed
#------------------------------------------------------------------------------
if wantUiWin:

	app = wx.App()
	window = wx.Frame(None, title = "Kicad to Creo Netlist", size = (600,400)) 
	panel = wx.Panel(window)

	sizer = wx.GridBagSizer(0, 0)

	#--------------------------------------------------------------------------
	# Row 0
	# Check Boxes and write button
	outputGroupFrame = wx.StaticBox( panel, label = "Select Output" , size = (140,60),pos = (10,10))
	mkCreoBtn = wx.CheckBox(outputGroupFrame, label = 'Creo Xml', pos = (10,20)) 
	mkSwBtn = wx.CheckBox(outputGroupFrame, label="SolidWorks csv", pos = (10,40))
	sizer.Add(outputGroupFrame, pos = (0, 0), flag = wx.ALL, border = 5)
	mkCreoBtn.SetValue(True)	
	
	btn = wx.Button( panel, label = "Write File(s)", size = (100,70)) 
	btn.Bind(wx.EVT_BUTTON, bar) 
	sizer.Add(btn, pos = (0, 1), flag = wx.ALIGN_RIGHT | wx.RIGHT | wx.TOP | wx.BOTTOM, border = 5)

	#--------------------------------------------------------------------------
	# Row 1
	# Output filename and Back annotation button
	lbl = wx.StaticText( panel, label = "Output Filename:") 	
	sizer.Add( lbl, pos = (1, 0), flag = wx.ALIGN_BOTTOM | wx.LEFT | wx.TOP, border = 5 )

	backBtn = wx.Button(panel, label="Back Annotate", size = (100,-1) )
	backBtn.Bind(wx.EVT_BUTTON, BackAnn) 
	sizer.Add(backBtn, pos = (1, 1), flag =  wx.ALIGN_RIGHT | wx.RIGHT | wx.TOP | wx.BOTTOM, border = 5)

	#--------------------------------------------------------------------------
	# Row 2
	# Filename entry box Span both columns
	fNameEntry = wx.TextCtrl( panel, size = ( 250, -1 ) )
	sizer.Add(fNameEntry, pos = (2, 0), span = (1, 2), flag = wx.EXPAND | wx.LEFT | wx.RIGHT, border = 5 )

	baseName = os.path.basename(creoLogicalFileName)
	fNameEntry.SetValue( baseName )

	#--------------------------------------------------------------------------
	# Row 3
	# Logging window, Span both comlumns
	# https://stackoverflow.com/questions/2819791/how-can-i-redirect-the-logger-to-a-wxpython-textctrl-using-a-custom-logging-hand
	st = wx.TextCtrl(panel, wx.ID_ANY, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH | wx.TE_BESTWRAP)
	sizer.Add( st, pos = (3, 0), span = (1, 2), flag = wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border = 1)
		
	sizer.AddGrowableRow( 3 )		#this makes the textcontrol to span
	sizer.AddGrowableCol( 1 )		#this makes the textcontrol to span
	font1 = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
	st.SetFont(font1)

	# Create textLogger
	text_handler = TextHandler(st)
	# Add the handler to logger
	logger = logging.getLogger()
	logger.addHandler(text_handler)
	#set level to print out all. Otherwise this will ignore the debug an info prints.
	logger.root.setLevel(logging.NOTSET)

	#--------------------------------------------------------------------------
	# Row 4
	# Statusbar
	lbl_progress = wx.StaticText(panel, label = "Status", size = (250,-1), style = wx.TE_READONLY | wx.BORDER_SUNKEN )
	sizer.Add(lbl_progress, pos = (4, 0), flag = wx.ALIGN_LEFT | wx.LEFT | wx.TOP | wx.BOTTOM , border = 2)
	
	progress = wx.Gauge(panel, range = 100, size = (150, -1), style = wx.GA_HORIZONTAL )
	sizer.Add( progress, pos = (4, 1), flag = wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.TOP | wx.BOTTOM, border = 5)


	sizer.SetMinSize((600, 400) ) 			#works for the panel sizer... Main window can still be resized
	panel.SetSizerAndFit(sizer)				
	sizer.SetSizeHints(window)				# uses main frame as size for the panel sizer.

	window.Show(True)
	app.MainLoop()
	
else:
	writeFileHeader( creoLogicalFileName )
	#------------------------------------------------------------------------------
	# Process the commands in console mode
	#------------------------------------------------------------------------------
	# Process Components (Connectors)
	print( "Writing Components, Connectors:" )
	print( "-------------------------------" )
	components = xmlWriteCompData.xmlWriteCompData()
	components.writeCompData(netlist,creoLogicalFileName)
	print( components.getInfoStr(), file=sys.stdout )
	print( components.getWarningStr(), file=sys.stdout )
	print( components.getErrorStr(), file=sys.stderr )

	# Process Spools (Wires, Cables)
	print( "Writing Spools (Wires, Cables)" )
	print( "------------------------------" )
	spools = xmlWriteSpools.xmlWriteSpools()
	spools.writeSpoolData(netlist,creoLogicalFileName)
	print( spools.getWarningStr(), file=sys.stdout )
	print( spools.getErrorStr(), file=sys.stderr )
	print("Spools Found and Created")
	print( spools.printCblSpoolNames())

	# Make connections
	print( "\nWriting From: To: Information" )
	print( "-----------------------------" )
	connections = xmlWriteConnections.xmlWriteConnections(spools)
	connections.writeConnections(netlist,creoLogicalFileName)
	print( connections.getWarningStr(), file=sys.stdout )
	print( connections.getErrorStr(), file=sys.stderr )
	writeFileEnd( creoLogicalFileName )

# End file

