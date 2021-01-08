# kicadcreo
Export logical data from kicad to creo harness 

Target of this project is to produce Creo Schematic compatible output to Creo parametic 3d program (Creo 4.0 M070).

PTC Creo is one of the "big" 3d parametric design softwares. Other similar products are Solidworks, Catia, Autocad Inventor, Onshape etc. One advantage of these programs is that they let you model every detail of your product. You can import pcb's using the IDF format and you can also route cables to your end product. The cad program will give you the needed cable lengths and cable drawings.

## Changes
2021.01.08
1. Added support for shielded cable.
1. Added option for ktinker interface.
1. Added support for hierarchical sheets. Mainly this means that backannotation goes through all sheets in design. If you use same schematic multiple times then the back annotation works only to the first instance of the sheet. Other sheets with the same name will have same wire lengths and part numbers as the first sheet. In creo, however, you can have totally different wire lengts and individual part numbers...  So don't use the same schematic multiple times unless you mean to use the same cables in all instances...

Scripts may still contain lots of "Features"... but they are usually easily fixed encountered.

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

## Using with Kicad

You can add the command to "Generate Bill of Materials". Add command with the "+" sign
Create Creo Schematic xml-File
* python "C:\directory_where_the_pythons_script_is/kicadToCreo.py" "%I" "%O"
Back annotate Creo Schematic xml-file
* python "C:\directory_where_the_pythons_script_is/xmlReadCreo.py" "%I" "%O"

Note: For back annotation the filename must be same as the xxx.sch file except it must end with xxx_creoin.xml.

You can add the command to "Generate Netlist". Add command with the "Add Plugin"-button.
Add Netlist Command
* python "C:\directory_where_the_pythons_script_is/kicadToCreo.py" "%I" "%O" "tkinter"

With the graphical interface you can generate the xml with one button and back-annotate with another button.
With the netlist option you can also generate the Creo Shematic file to any directory. Bom-button will generate the files to the directory where the schematic is.







