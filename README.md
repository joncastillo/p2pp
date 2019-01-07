# p2pp - **Palette2 Post Processing tool for Slic3r PE**


**Tested with version 1.41.2 and 1.42.0 Alpha 1**
earlier versions may generate different code patterns and may not work correctly


## Purpose

Allow Palette 2 users to exploit all freatures and functionality of the palette 2 (Pro) with the Slic3r PE functionality for multi material printing including:

- use of variable layers without blowing up the wipe tower
- wipe to waste object
- wipe to infill
- configurable option to create more filament at the end of the print 

P2pp currently only works for devices in a connected setup.  It does not generate the required sequences to meet the Pause-based pings in accessory mode.

## Functionality

P2pp is a python script with a  shell script/batch file wrapper.

P22pp works as a post processor to GCode files generated by Splic3r PE, just like Chroma does.   If does however not create any new code for wipe towers etc, it just adds Palette 2 MCF information codesto the file.  The script is triggered automatically when exporting GCode or when sending information to the printer so no manual additional step is required.  

**IMPORTANT**

Prior to using the script it is important to *setup the printer according to the specifications set by Mosaic* ( this includes full calibration using canvas or Chroma).

## Installation

Clone this Github repository to a zip file and extract this zipfile to a location of your choice.  In addition you will need either python 2.7 or python 3 to be installed on your machine. 


### WINDOWS 

edit the .bat file with the correct path to the .py script.  


### Unix / Mac OSX

Further when running on a unix-flavoured system (Mac OSX or Linux), you will need to make the script p2pp.sh executable:
 

```
   cd place_where_you_extracted_the_zip_file
   
   chmod 755 p2pp.sh
```


you van test now by typing


```
   ./p2pp.sh
```

this should result in the following error:
```
usage: P2PP.py [-h] -i INPUT_FILE [-d OUTPUT_FILE] [-o SPLICE_OFFSET] [-g GUI]
               [-p PRINTER_PROFILE] [-s SILENT]
P2PP.py: error: argument -i/--input-file: expected one argument
```

This indicates all files are properly setup and execute correctly

The remainder of the configuration is done in Slic3r PE

## Configuration of Slic3r PE:

**!!! FOR NOW THERE IS NO ERROR CHECKING ON THE P2PP CODES SO MAKE SURE TO ENTER EVERYTHINGS AS SHOWN INCLUDING CAPITALS ETC**

If you want to take a headstart you can import the configuration file in the splic3r_templates subfolder.  This file contains PLA Fileament, print and printer definitions.   

At least perform the sceps below to enter the Print Profile ID and the pointer to the sh/bat script depending on your operating system.  

### Printer Settings

**Add the following information to the SLic3r Printer Settings startup g-code

when you imported the config profile, you will only have to update the first line.  The printer profile can be retrieved from any mfc.gcode file generated by chroma or canvas.  Make sure to use take this from a profile with which the printer was calibrated to avoid extra calibration work.

One of the first lines of the mcf.gcode file will contain the O22 command. 

e.g. O22 De827315ff39aaaaa

Take everythong after **O22 D** and use that as your printer Profileas follows.  Note your ID will differ and making a mistake will trigger the printer in recalibration!!
```
;P2PP PRINTERPROFILE=e827315ff39aaaaa
;P2PP SPLICEOFFSET=30
;P2PP MINSTARTSPLICE=100
;P2PP MINSPLICE=70
```
SPLICEOFFSET defined the amount of mm added to the first splice.  It works in a simalr way as setting the transition position % from Chroma and Canvas.  Here the value is a fiexed length.  I found 30mm to be a good position resulting in perfect prints on my setup.   You may want to tweak this function if you find the transition happens too early or too late.

If you want the splice length warnings to contain layer information you also need to add the following information to the **AFTER LAYER CHANGE GCode of your Slic3r Printer Profile**.  Text between [] will be automatically converted to actual values by Slic3R PE when exporting the GCode to disk or to the printer.  This step is not reauired if you are using the imported sample profile

```
;AFTER_LAYER_CHANGE
;LAYER [layer_num]
```

The splice process is now defined in the Statup GCode of the Slic3r  PE *Printer profile*.  Based on the materials a user can define heat/compression/cooling additional.  The MATERIAL_DEFAULT setting provides a configurable fallback in case no profile is defined for the material combination.   **NOTE:**  these entries are not symmetrical, ie you need to define both directions in order to specify a complete process; This step is already included in the sample profile.  The definition is as per standard Chroma and Canvas profiles.  Order of parameters is heat/compression/cooling so.  Default is all 0 as per standard in Chroma and Canvas

```
;P2PP MATERIAL_DEFAULT_0_0_0
;P2PP MATERIAL_PVA_PVA_0_0_0
;P2PP MATERIAL_PVA_PLA_0_0_0
;P2PP MATERIAL_PLA_PLA_0_0_0
```

### Print Settings

Under **Print Settings - Output options** you will find the possibility to add a **post-processing script**.  Put the full name of the .sh (unix/Mac OSX) or .bat  (Windows) in this window.  Include the full path (don't use ~ for OSX).  Add no parameters.

```
e.g /yourpath/p2pp.sh
or on a windows machine
e.g. c:\yourpath\p2pp.bat
```

**IMPORTANT: the minimal first slice length is 100mm, required to make the filament reach the outgoing drive, minimum slice distance for following slices  can be set as low as 40 this will impact the speed at which filament can be created so print speed may have to be adjusted accordingly**


### Filament Settings

Add the following lines exactly as shown to *EACH* filament profile you want to use with the palette 2.
These changes will not interfere with the normal working under other profiles as only comments are added to the gcode file.

```
;P2PP FN=[filament_preset]
;P2PP FT=[filament_type]
;P2PP FC=[extruder_colour]
```


## Usage

When setup correctly the script will be triggered automatically from Slic3r PE and exported files will cointain the mcf header reauired for palette operation.   This functionality will only be enabled when selecting the right print/filament and printer profiles so when selecting any other profiles, single filament file generation will happen as before.

During the conversion the script may come up with a window stating possible warninngs.  If slices are too short, increase the purge volumes until the required length is met (or lower the P2PP_MINSPLICE setting).   If the start slice is too short, you can add a brim or skirt to use more filament in the first color.

On your first prints make sure to review the output file to make sure it contains the Omega header. (bunch of comands starting this capital letter O (oh)

The purge settings in Slic3r PE are defined under the purge volumes settings.  This button is only visible on the plates screen when a multimaterial serup is selected using one extruder only.   The information entered in this screen is volumetric. This means that you have to roughly multiply the number in these fields by a factor 2.4 in order to get the filament length.
I successfully tested with an 180mm3 value (75mm filament)

Happy printing.


## Acknowledgements

Thanks to Tim Brookman for the co-development of this plugin and for all who tested and provided feedback.


Good luck & happy printing !!!



