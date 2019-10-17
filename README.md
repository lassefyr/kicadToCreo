# kicadcreo
Export logical data from kicad to creo harness 

Target of this project is to produce Creo Schematic compatible output to Creo parametic 3d program (Creo 4.0 M070).

PTC Creo is one of the "big" 3d parametric design softwares. Other similar products are Solidworks, Catia, Autocad Inventor, Onshape etc. One advantage of these programs is that they let you model every detail of your product. You can import pcb's using the IDF format and you can also route cables to your end product. The cad program will give you the needed cable lengths and cable drawings.

## Getting Started

You can copy the entire repository to your PC.

### Installing

You need to setup the script in Kicad sch. Press the bom button and add plugins
- kicadToCreo.py (coverts your schematic to creo schematic netlist)
- xmlReadCreo.py (read creo schematic netlist, when done, and updates lenghts and part numbers to a new kicad schematic.


## Testing

There are a test schematic in directory /kicad_sample_design
1. "testpcb.sch" contains the original design file.
	- connectors are in Cabling.lib (separate directory)
	
2. "testpcb_creo.sch" is the back annotated schematic. 
	- Harness names and lenghts are shown in this schematic.
	
3. creo_testcable.pdf
	- how the cable looks like in creo (.pdf snapshot)
	- All connectors used are under creo_connectors directory

The creo 3d-connectors that were used on this design are on directory "creo_connectors"


