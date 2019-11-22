# kicadcreo
Export logical data from kicad to creo harness 

Target of this project is to produce Creo Schematic compatible output to Creo parametic 3d program (Creo 4.0 M070).

PTC Creo is one of the "big" 3d parametric design softwares. Other similar products are Solidworks, Catia, Autocad Inventor, Onshape etc. One advantage of these programs is that they let you model every detail of your product. You can import pcb's using the IDF format and you can also route cables to your end product. The cad program will give you the needed cable lengths and cable drawings.

## Getting Started

You can copy the entire repository to your PC.

### Installing

You need to setup the script in Kicad eeschema. Press the bom button and add plugins (path to the python scripts that you downloaded)
- kicadToCreo.py (converts your schematic to creo schematic netlist)
- xmlReadCreo.py (when done routing in Creo, this script reads the Creo schematic netlist and updates lenghts and part numbers to Kicad schematic file. New filename will be originalschemafilename+"_creo".sch)

## Testing

There are a test schematic in directory /kicad_sample_design
1. "testpcb.sch" contains the original design file.
	- connectors are in Cabling.lib (separate directory)
	
2. "testpcb_creo.sch" is the back annotated schematic. 
	- Harness names and lenghts are shown in this schematic.
	
3. creo_testcable.pdf
	- how the cable looks like in creo (.pdf snapshot)
	- All connectors used are under creo_connectors directory

The creo 3d-connectors that were used on this design are on directory "creo_connectors". You check these to see how the Pins are named on the Creo symbols.

## Back Annotation
Create an Schematic xml file from creo. Name it "Kicad design filename"+**_creoin.xml** and copy it into the Kicad design directory (where the original kicad schematic is). Run the xmlReadCreo.py from Kicad Schematic. You will get another schematic file where wire lenghts are displayed.

## Additions
2019-11 tried to add Sheath spools but failed. It seems that there is a bug in Creo. 
Read the PTC article CS312099 "Sheath type spools are exported to NWF as cable spool and to XML as wire in Creo Parametric
Applies to Creo Parametric 4.0 to 6.0."


