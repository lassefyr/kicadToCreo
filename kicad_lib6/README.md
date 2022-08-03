# Kicad 6.x Library file

This is the 5.x library converted to version 6.0. 
From now on I will only maintain the 6.x version.

File includes all Kicad cabling symbols.

**Typical Connector Symbol parameters**
| Name         | Value                                                              |
| ------------ | ------------------------------------------------------------------ |
| Reference	   | J? (automatically numbered by Kicad) |
| Value        | Symbol name. This is used as a part name for creo unless there is a Modelname parameter specified |
| Datasheet    | Optional link to data sheet |
| Term_name    | Name of the default Crimp Terminal (terminator in Creo) |
| Internal_len | This length is added to the cable length in Creo. Default is 5 if not defined. |
| Vendor       | Optional but good to have |
| Vendor_pn    | Optional but good to have |


**Typical Wire Spool Symbol parameters**
| Name         | Value                                                              |
| ------------ | ------------------------------------------------------------------ |
| Reference | W? (1automatically numbered by Kicad) |
| Value | 18awg_bk_1 Becomes the wire name |
| Footprint | Empty |
| Datasheet | Optional link to data sheet |
| Color | Color of the Wire |
| Units | mm (millimeters is the only implemented measurement at the moment) |
| Thickness | Thickness of the Wire |
| Min_bend_radius | Minimum bending radius |
| Gauge | 18 (for awg 18) |
| Density | Cable density. Kilograms/mm in our system |
| Vendor_pn | Shown in Creo Drawing |
| Length | Can be read from Creo logical file (after routing) |
| Harness_name | Can be read from Creo logical file (after routing). This is the part name that is created in Creo. |


**Typical Cable Spool Symbol parameters**
| Name         | Value                                                              |
| ------------ | ------------------------------------------------------------------ |
| Reference    | CBL? (automatically numbered by Kicad) |
| Value        | 24awgx4_u_4_3mm Becomes the spool name |
| Footprint    | Empty |
| Datasheet    | Optional link to data sheet |
| Num_conductors | Number of coductors |
| Color          | Sheath Color |
| Thickness      | Outer thickness of the Cable |
| Density        | Cable density. Kilograms/mm in our system |
| Min_bend_radius | Minimum bending radius |
| Sub_thickness  | Thickness of the inner wires |
| Color1         | Color of the first inner cable |
| Colorx         | As many colors needed as specified by "Num_coinductors"-parameter |
| Vendor         | Shown in Creo Drawing  |
| Vendor_pn      | Shown in Creo Drawing |
| Length         | Can be read from Creo logical file (after routing) |
| Harness_name   | Can be read from Creo logical file (after routing). This is the part name that is created in Creo. |
| Type           | Prefab |
| Gauge          | 24 (for awg 24) |




