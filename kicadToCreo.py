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
#from __future__ import standard_library
#standard_library.install_aliases()


# Import the KiCad python helper module
import kicad_netlist_reader
import sys
import os
import xmlWriteCompData
import xmlWriteSpools
import xmlWriteConnections
if sys.version_info.major < 3:
	import Tkinter as tk
	import ttk as ttk
else:
	import tkinter as tk
	import tkinter.ttk as ttk
	
import logging
import threading


# Text Handler class for the tKinter Interface
class TextHandler(logging.Handler):
	"""This class allows you to log to a Tkinter Text or ScrolledText widget"""
	def __init__(self, text):
		# run the regular Handler __init__
		logging.Handler.__init__(self)
		# Store a reference to the Text it will log to
		self.text = text
#		Set different Background colors for error and warning messages. You can also change 
#		the foreground color with (or without) by adding e.g. "foreground='red'" 
		self.text.tag_config("error", background="#cc0000",  font = ('Courier', 12, 'bold'))
		self.text.tag_config("warn", background="#ff8800",  font = ('Courier', 12, 'bold'))

	def emit(self, record):
		msg = self.format(record)
		def append():
			self.text.configure(state='normal')
			if(record.levelname == "ERROR"):				
				self.text.insert(tk.END, msg + '\n',"error")
			elif(record.levelname == "WARNING"):
				self.text.insert(tk.END, msg + '\n',"warn")
			else:
				self.text.insert(tk.END, msg + '\n')
			self.text.configure(state='disabled')
			# Autoscroll to the bottom
			self.text.yview(tk.END)
		# This is necessary because we can't modify the Text from other threads
		self.text.after(0, append)
	
if len(sys.argv) < 3:
    print("Usage ", __file__, "<netlist.xml> <output file> <optional tkinter>", file=sys.stderr)
    sys.exit(1)

# Check whether we want console or tkinter app
tKinterWin = False
if len(sys.argv) == 4:
	tKinterWin = True

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
		if(tKinterWin):
			logger.info( "Valid utf-8" )
		else:
			print("Valid utf-8", file = sys.stdout)
		f.close()
	except UnicodeDecodeError:
		f.close()			
		if(tKinterWin):
			logger.error( "Invalid utf-8" )			
		else:
			print("invalid utf-8", file = sys.stderr)
		
#------------------------------------------------------------------------------
#	Progress Bar for the tKinter interface
#------------------------------------------------------------------------------
def bar(): 
	import time 
	
	# Clear Logger buffer. You must first set the state to normal before clearing.	
	st.configure(state='normal')
	st.delete(1.0, tk.END)
	st.configure(state='disabled')	
	logger.info('Started ' + time.strftime('%H:%M:%S'))
	writeFileHeader( creoLogicalFileName )
	
	progress['value'] = 30	
	logger.info('Writing component Information')
	# Write Components ------------------------------------
	components = xmlWriteCompData.xmlWriteCompData()
	components.writeCompData(netlist,creoLogicalFileName)
	# Get connection warnings and errors
	logger.info( components.getInfoStr() )
	logger.warning( components.getWarningStr() )
	logger.error( components.getErrorStr() )
	
	st.update() #this works
	window.update_idletasks() 
	# time.sleep(4) 
	
	progress['value'] = 66
	logger.info('\nWriting Spools')
	# Write Spools ----------------------------------------
	spools = xmlWriteSpools.xmlWriteSpools()
	spools.writeSpoolData(netlist,creoLogicalFileName)
	# Get Spool warnings and errors
	logger.warning( spools.getWarningStr() )
	logger.error( spools.getErrorStr())
	logger.info( 'Spools Found and Created...' )
	logger.info( spools.printCblSpoolNames() )	
	
	st.update() #this works
	window.update_idletasks() 

	progress['value'] = 95
	logger.info('\nWriting Connections')
	# Write Connections -----------------------------------
	connections = xmlWriteConnections.xmlWriteConnections( spools )
	connections.writeConnections( netlist,creoLogicalFileName )
	# Get Connection warnings and errors
	logger.warning( connections.getWarningStr() )
	logger.error( connections.getErrorStr() )

	st.update() # this works
	
	progress['value'] = 100
	writeFileEnd( creoLogicalFileName )

def BackAnn():
	import time 
	import xmlReadCreo
	
	# Clear Logger buffer. You must first set the state to normal before clearing.	
	st.configure(state='normal')
	st.delete(1.0, tk.END)
	st.configure(state='disabled')	
	logger.info('Started ' + time.strftime('%H:%M:%S'))
	
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

#------------------------------------------------------------------------------
# Create the tKinter window if needed
#------------------------------------------------------------------------------
if tKinterWin:
	window = tk.Tk()
	window.title("Kicad to Creo Netlist")
	window.geometry("600x400")

	# Allow only height to be resized...
	window.resizable(False, True)

	createCreoXmlVar = tk.IntVar()
	createSwCsvVar = tk.IntVar()

	outputGroupFrame = tk.LabelFrame(window, text = "Select Output", padx=10, pady=10)
	outputGroupFrame.grid( row=0, column=0, sticky="w", padx = 10 )

	mkCreoBtn = tk.Checkbutton(outputGroupFrame, text="Creo Xml", variable=createCreoXmlVar, onvalue = 1, offvalue = 0)
	mkCreoBtn.grid(row=0, column=0, sticky="w")

	mkSwBtn = tk.Checkbutton(outputGroupFrame, text="SolidWorks csv", variable=createSwCsvVar, onvalue = 1, offvalue = 0)
	mkSwBtn.grid(row=1, column=0, sticky="w")

	lbl = tk.Label(window, text="Output Filename:")
	lbl.grid(row=1, column=0, sticky = "w", padx=5, pady=5)

	baseName = os.path.basename(creoLogicalFileName)
	fileNametext = tk.StringVar()
	fNameEntry = tk.Entry(window, textvariable = fileNametext )
	fileNametext.set(baseName)
	fNameEntry.grid(row=2, column=0, rowspan = 2, sticky = "wens", padx=5)

	#lbl_fName = tk.Label(window, text = baseName, relief="raise", anchor = "w" )
	#lbl_fName.grid(row=2, column=0, rowspan = 2, sticky = "wens", padx=5)

	lbl_progress = tk.Label(window, text = "Progress", padx=5)
	lbl_progress.grid(row=2, column=1, sticky = "wens")

	btn = tk.Button(window, text="Write File(s)", command = bar)
	btn.grid(row=0, column=1, sticky = "wens", padx = 5,  pady=5 )

	backBtn = tk.Button(window, text="Back Annotate", command = BackAnn)
	backBtn.grid(row=1, column=1, sticky = "wens", padx = 5,  pady=5 )


	progress = ttk.Progressbar(window, orient = "horizontal", length = 100, mode = "determinate")
	progress.grid(row=3, column=1, sticky = "wens", padx = 5)

	if sys.version_info.major < 3:
		from ScrolledText import ScrolledText
	else:
		from tkinter.scrolledtext import ScrolledText

	st = ScrolledText(window, state='disabled', width=60, height = 10)
	st.configure(font='TkFixedFont')

	# Make the scroll window resizing...
	tk.Grid.rowconfigure(window, 4, weight=1)
	tk.Grid.columnconfigure(window, 0, weight=1)
	st.grid(row=4, column=0, columnspan=2, sticky="nswe", pady=5, padx=5)

	# Create textLogger
	text_handler = TextHandler(st)

	# Add the handler to logger
	logger = logging.getLogger()
	logger.addHandler(text_handler)
	#set level to print out all. Otherwise this will ignore the debug an info prints.
	logger.root.setLevel(logging.NOTSET)
	st.update()
	
	setWindowHeight = outputGroupFrame.winfo_height()
	setWindowHeight += lbl.winfo_height()
	setWindowHeight += fNameEntry.winfo_height()
	setWindowHeight += st.winfo_height()

	mystring =str(st.winfo_width()+25)+"x"+str(setWindowHeight+22)
	window.geometry(mystring)

	window.update()
	window.mainloop()
	
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

