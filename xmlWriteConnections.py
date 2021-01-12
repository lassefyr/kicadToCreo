#
# MIT license
#
# Part of kicadToCreo script
# This sample was created from one of the kicad bom scripts
# Write connections from connector to connector
#
# Copyright (C) LasseFyr 2019.
#
# This has been tested only with Creo 4.0 070
#
# Changelog:
# 2019-11-26 Single sided cable connections generated faulty xml. Added ignore unless both sides of the 
#            cable are connected

"""
    @package
    Generate a net list file.

    Command line: 
    Run kicadToCreo script from Kicad eeschema with default parameters "%I" "%O"
"""

from __future__ import print_function
import kicad_netlist_reader
from xmlWriteSpools import xmlWriteSpools
import sys 
#from termcolor import colored

class xmlWriteConnections(xmlWriteSpools):

	def __init__(self, spoolClass):
		self.ENTRY_PORT = "PIN_"
		self.PORT_TYPE = "Electrical"
		self.GROUPING = "round"	
		self.INTERNAL_LEN = "5"
		self.TERM_AUTO_ASSIGN = "TRUE"
		self.idNum = 1				# This is the first component
		self.spoolClass = spoolClass
		self.__errorString = ""
		self.__warningString=""	
        
	def find_net(self, netlist, ref, pin):
		for net in netlist.nets:
			for node in net.getChildren('node'):
				if node.get("node", "ref") == ref and node.get("node", "pin") == pin:
					return net
		return None
            
	def find_matching_node(self, netList, netName):
		if not netName:
			return None

		for net in netList.nets:
			if netName == net.get("net", "name"):   			# Net name is the same 
				for node in net.getChildren('node'):	
					readRef = node.get("node", "ref") 
					if readRef[:1]!="W" and readRef[:3]!="CBL":	# This is the component not Wire or Cable
						return node
		return None 
		            
	def writeConnections(self, netlist, outputFileName):
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
		
		components = netlist.getInterestingComponents()
		
		# self.spoolClass.printCblSpoolNames()
		
		for comp in components:
			refDes = comp.getRef()
			part = comp.getLibPart()
			
			if refDes[:1] != "W" and refDes[:3] != "CBL":
				continue

# Find first spool, Check both ends and net names where they are connected			
			spoolName = comp.getField("Value")
			if not spoolName:
				self.writeWarningStr(refDes+ " no Spool name defined!")
				spoolName = "NOT_DEFINED"
				continue			
				

# Component NUM_OF_PINS how many pins in this component-----------------------------------								
			pins = part.element.getChild('pins')
			if pins:   # more than one
				howManyPins = len(pins.getChildren())
				# check if shielded cable
				thisIsShielded = comp.getField("Shield")
				if not thisIsShielded:
					thisIsShielded = "None"
#				print("Pins "+str(howManyPins))
			else:		# no Pins continue	
				continue
			
			thisIsCbl = False
			if refDes[:3] == "CBL":
				thisIsCbl = True
				print("<CONNECTION name=\""+refDes+"\" context=\"NONE\" spoolID=\"cbl_"+spoolName+"\" type=\"ASSEMBLY\">", file = fout)
				print("<SYS_PARAMETER id=\"cbl_"+refDes+"\" />", file = fout)
				print("<PARAMETER name=\"LAYER\" value=\"DEF_LINES\"/>", file = fout)
				print("<PARAMETER name=\"UNIT\" value=\"MM\"/>", file = fout)
				print("</CONNECTION>", file = fout)
					
			myCounter = 0
			lastWire = False
			
			for i in range(1, howManyPins, 2): #(each net has two counter parts)
				connTableID = []
				myCounter += 1
				
#				For shielded Cable the last wire is the shield wire.				
				if (i+1) == howManyPins:
					lastWire = True

#				Find both ends of wire. Single ended wires are generally an error.
#				Only Shielded cables can be single ended.					
				tempNet = self.find_net(netlist, refDes, str(i))
				if ( tempNet ):
					wireNet1 = tempNet.get( "net", "name" )
				tempNet = self.find_net(netlist, refDes, str(i+1))
				if ( tempNet ):
					wireNet2 = tempNet.get( "net", "name" )

				scannedNode1 = self.find_matching_node(netlist, wireNet1)
				scannedNode2 = self.find_matching_node(netlist, wireNet2)
				
				if( thisIsCbl ):
					getSpoolIndex = self.spoolClass.getCblSpoolId(spoolName+"-"+str(myCounter))
					if( getSpoolIndex<0 ):
						self.writeErrorStr("No spoolIndex for "+spoolName+": pin:"+str(myCounter))
					else:
						cblId = "sp"+str(getSpoolIndex+1)
						print("<CONNECTION name=\""+refDes+"_"+str(myCounter)+"\" context=\"CONNECTION\" parentID=\"cbl_"+refDes+"\" spoolID=\""+cblId+"\" type=\"SINGLE\">", file = fout) #conductorName=\""+str(myCounter)+"\"
				else:
					print("<CONNECTION name=\""+refDes+"\" type=\"SINGLE\" subType=\"WIRING_WIRE\" context=\"NONE\" spoolID=\"w_"+spoolName+"\" >", file = fout)
			
				if(  thisIsCbl ):
					print("<SYS_PARAMETER id=\"conn_"+refDes+"_"+str(myCounter)+"\" />", file = fout)
# 					If this is shielded cable and the last connections
					if lastWire and thisIsShielded!="None":					
						print("<PARAMETER name=\"TYPE\" value=\"SHIELD\"/>", file = fout)
					
				else:	
					print("<SYS_PARAMETER id=\"conn_"+refDes+"\" />", file = fout)

				print("<PARAMETER name=\"LAYER\" value=\"DEF_LINES\"/>", file = fout)

				if scannedNode1:
					matchRef = scannedNode1.get("node", "ref")
					matchPin = scannedNode1.get("node", "pin")
					connTableID.append("\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"\"")
					
					print("<NODE name=\""+matchRef+"_"+matchPin+"_"+refDes+"\" type=\"COMPONENT\" >", file = fout)
					print("<SYS_PARAMETER id=\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"\" />", file = fout)
					print("<ATTACH_TO compORconnID=\"comp_"+matchRef+"\" nodeORportID=\"comp_"+matchRef+"_"+matchPin+"\"/>", file = fout)
					print("</NODE>", file = fout)
				else:
					self.writeErrorStr("Missing connection for nod "+refDes+": pin:"+str(i))					
					matchRef = scannedNode2.get("node", "ref")
					matchPin = scannedNode2.get("node", "pin")
					
					if( thisIsCbl and lastWire and thisIsShielded!="None" ):
						connTableID.append("\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"_SH\"")
						print("<NODE name=\""+matchRef+"_"+matchPin+"_"+refDes+"_SH\" type=\"POINT\" >", file = fout)
						print("<SYS_PARAMETER id=\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"_SH\" />", file = fout)
						print("</NODE>", file = fout)
						
				if scannedNode2:
					matchRef = scannedNode2.get("node", "ref")
					matchPin = scannedNode2.get("node", "pin")
					connTableID.append("\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"\"")

					print("<NODE name=\""+matchRef+"_"+matchPin+"_"+refDes+"\" type=\"COMPONENT\" >", file = fout)
					print("<SYS_PARAMETER id=\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"\" />", file = fout)
					print("<ATTACH_TO compORconnID=\"comp_"+matchRef+"\" nodeORportID=\"comp_"+matchRef+"_"+matchPin+"\"/>", file = fout)
					print("</NODE>", file = fout)
				else:
					self.writeErrorStr("Missing connection for nod "+refDes+": pin:"+str(i+1))
					matchRef = scannedNode1.get("node", "ref")
					matchPin = scannedNode1.get("node", "pin")

					if( thisIsCbl and lastWire and thisIsShielded!="None" ):
						connTableID.append("\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"_SH\"")
						print("<NODE name=\""+matchRef+"_"+matchPin+"_"+refDes+"_SH\" type=\"POINT\" >", file = fout)
						print("<SYS_PARAMETER id=\"comp_"+matchRef+"_"+matchPin+"_"+refDes+"_SH\" />", file = fout)
						print("</NODE>", file = fout)						
				
# Component print Connection -------------------------------------------------------------											
				if (len(connTableID) >= 2):		
					print("<SEGMENT name=\"seg_"+refDes+"_"+str(myCounter)+"\" >", file = fout)
					print("<ATTACH node1ID="+connTableID[0]+" node2ID="+connTableID[1]+" />", file = fout)
					print("</SEGMENT>", file = fout)		

				print("</CONNECTION>", file = fout)

		if isOutputFileOpen == True:
			fout.close()
			isOutputFileOpen = False											


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
			self.__errorString="Connections: No Errors!"			
		return self.__errorString 
		
	def clearErrorStr( self ):
		self.__errorString=""

	def writeWarningStr( self, wStr ):
		#print( wStr )
		self.__warningString += wStr
		
	def getWarningStr( self ):
		if self.__warningString == "":
			self.__warningString="Connections: No Warnigns!"
		return self.__warningString 
		
	def clearWarningStr( self ):
		self.__warningString=""		
		
		
			
'''			
			for connector in components:
				connectorRef = connector.getRef()
				
				if connectorRef[:1] != "J":
					continue
				
				jxPart = connector.getLibPart()	
				sys.stdout.write("\033[1;31m")
				print("Connector" + connectorRef)
				sys.stdout.write("\033[0;0m") 
				 
				pins = jxPart.element.getChild('pins')
				if pins:
					
					for pin in pins.getChildren():
						connectorNet = self.find_net (netlist, connectorRef, pin.get("pin", "num") )
						connNetName = connectorNet.get("net", "name" )
						print("Net =" + connNetName),
						
						if (connectorPin1Net == connNetName) or (connectorPin2Net == connNetName):
							conn_spoolRef = refDes					# e.g. W1, W2 
							conn_spoolName = spoolName				# e.g. awg22_bl
							conn_compName = connectorRef			# e.g J1 or J2
							conn_pinNbr	  = pin.get("pin", "num")	# Pin number of the component
							conn_netName = connNetName				# NetName e.g. Net-(J2-Pad1)
								
							print("<NODE name=\""+conn_compName+"_"+conn_pinNbr+"\" type=\"COMPONENT\" >", file = fout)
							print("<SYS_PARAMETER id=\"conn_"+conn_compName+"_"+conn_pinNbr+"\" />", file = fout)
							print("<ATTACH_TO compORconnID=\""+conn_compName+"\" nodeORportID=\"conn_"+conn_compName+"_"+conn_pinNbr+"\"/>", file = fout)
							print("</NODE>", file = fout)
							connTableID.append("\"conn_"+conn_compName+"_"+conn_pinNbr+"\"")

			if (len(connTableID) == 2):
				print("<SEGMENT name=\"conn_"+refDes+"\" >", file = fout)
				print("<ATTACH node1ID="+connTableID[0]+" node2ID="+connTableID[1]+" />", file = fout)
				print("</SEGMENT>", file = fout)						
			else:
				print("List Length =="+str(len(connTableID)))
'''					
					
						
						
'''
for howmanypins/2 in spool   # 1 for normal spool 5 for 10 wire cable
								pins 1 and 2
								pins 3 and 4
								pins 5 and 6
								pins 7 and 8
								pins 9 and 10
								

pins = part.element.getChild('pins')
# Component NUM_OF_PINS how many pins in this component-----------------------------------					
	if pins:  #more than one
		howManyPins = len(pins.getChildren())
		
		for for i in range(1, howManyPins, 2): (each net has two counter parts)
			wireNet1 = self.find_net(netlist, refDes, str(i))
			wireNet2 = self.find_net(netlist, refDes, str(i+1))
			
			scannedNode = find_matching_node(netList, wireNet1)
			if scannedNode
				matchRef = scannedNode.get("node", "ref")
				matchPin = scannedNode.get("node", "pin")
				connTableID.append("\"conn_"+conn_matchRef+"_"+conn_matchPin+"\"")

			scannedNode = find_matching_node(netList, wireNet2)
			if scannedNode
				matchRef = scannedNode.get("node", "ref")
				matchPin = scannedNode.get("node", "pin")
				connTableID.append("\"conn_"+conn_matchRef+"_"+conn_matchPin+"\"")
				
	
	
	
	def find_matching_node(self, netList, netName):
		if !netName:
			return None
		
		for net in netList.nets:
			if netName == net.getChildred("name"):   	# Net name is the same 
				for node in net.getChildren('node'):	
					readRef = node.get("node", "ref") 
				 	if readRef:1]!="W":					# This is the component not the Wire
				 		return node
		return None 	 
			

'''