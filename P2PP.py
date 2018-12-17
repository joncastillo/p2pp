#!/usr/bin/pythonw

__author__ = "Tom Van den Eede"
__copyright__ = "Copyright 2018, Palette2 Splicer Post Processing Project"
__credits__ = ["Tom Van den Eede"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Tom Van den Eede"
__email__ = "P2PP@pandora.be"
__status__ = "Beta"


import struct
import sys
import os
import getopt



#########################################
# Variable default values
#########################################

DEBUG_MODE = True
DEBUG_MODE_INPUT_FILE = '/Users/tomvandeneede/Desktop/Lego.gcode'

graphicalUserInterface = True

# Filament Transition Table
# encode filament type in your GCode for Filament
# add the following line (without the leading #)
# ;P2PP FT%1
# this will tell the post processor that this is filament of type 1 (you can add as many numbers as you want

FilamentType    = [ 1,1,1,1 ]


FilamentTypeConversion   = {
    'PVA'   : 1,
    'SCAFF' : 1,
    'NGEN'  : 1,
    'PVA'   : 2,
    'PET'  : 3,
    'FLEX'  : 4,
    'ABS'   : 4,
    'HIPS'  : 4,
    'EDGE'  : 4
}

FilamentName    = [ "Unnamed", "Unnamed" ,  "Unnamed", "Unnamed"]

FilamentColor   = [ "FFFF00" , "FF00FF" , "00FFFF", "FF0000"]  #default colors when not set, Yellow, Purple, Cyan, Red

FilamentTransition = [
                       [False, False, False, False],
                       [False, False, False, False],
                       [False, False, False, False],
                       [False, False, False, False]
                    ]

FilamentHeat    = [
    ["D000" , "D000", "D000" , "D000"] ,  #D1x
    ["D000" , "D000", "D000" , "D000"] ,  #D2x
    ["D000" , "D000", "D000" , "D000"] ,  #D3x
    ["D000" , "D000", "D000" , "D000"]    #D4x
]
FilamentCompression = [
    ["D000" , "D000", "D000" , "D000"] ,  #D1x
    ["D000" , "D000", "D000" , "D000"] ,  #D2x
    ["D000" , "D000", "D000" , "D000"] ,  #D3x
    ["D000" , "D000", "D000" , "D000"]    #D4x
]
FilamentCooling = [
    ["D000" , "D000", "D000" , "D000"] ,  #D1x
    ["D000" , "D000", "D000" , "D000"] ,  #D2x
    ["D000" , "D000", "D000" , "D000"] ,  #D3x
    ["D000" , "D000", "D000" , "D000"]    #D4x
]

# printerprofile is a unique ID linked to a printer configuration profile in the Palette 2 hardware.
PrinterProfile = ''

# this variable is used for checking which filament strands are used throughout the print.   if a filament is used
# it is configured with a D{type} otherwise a D0 in the filament descriptor.   D0 will NOT be loaded during the initialization
FilamentUsed   = [False , False , False , False ]
O32Table = ""

# spliceoffset allows for a correction of the position at which the transition occurs.   When the first transition is scheduled
# to occur at 120mm in GCode, you can add a number of mm to push the transition further in the purge tower.  This srves a similar
# function as the transition offset in chroma
SpliceOffset = 0.0

# keeps track of the number of splices discovered in the print
SpliceCount    = 0

# these 2 varaibles are used to build the splice information table (Omega-30 commands in GCode) that will drive the Palette2
# the txt variable is just a comment text that is pasted after the palette header to present the information in a readble way
O30Table = ""
O30TableTxt = ""

# ping text is a text variable to store information abou the PINGS generated by P2PP.   this information is pasted after
# the splice information right after the Palette2 header
PingText = ""

# Pingcount is the number of Pings generated during the print
PingCount      = 0

# Hotswapcount is the number of hotswaps generated furing the print.... not sure what this is used for, this variable is
# only used to complete the header
HotSwapCount   = 0

# filament transition algorithms
AlgorithmCount = 0

# TotalExtrusion keeps track of the total extrusion in mm for the print taking into account the Extruder Multiplier set
# in the GCode settings.
TotalExtrusion = 0

# The next 3 variables are used to generate pings.   A ping is scheduled every ping interval.  The LastPing option
# keeps the last extruder position where a ping was generated.  It is set to -100 to pring the first PING forward...
# Not sure this is a good idea.   Ping distance increases over the print in an exponential way.   Each ping is 1.03 times
# further from the previous one.   Pings occur in random places!!! as the are non-intrusive and don't causes pauses in the
# print they aren ot restricted to the wipe tower and they will occur as soon as the interval length for ping is exceeded.

LastPing = -100
PingInterval   = 350
PingExp        = 1.03


#currenttool/lastLocation are variables required to generate O30 splice info.   splice info is generated at the end of the tool path
# and not at the start hance the reauirement to keep the toolhead and lastlocation to perform the magic
currenttool    = -1
LastLocation = 0


# Capture layer inbformation for short splice texts
Layer = "No Layer Info"

#Extrusionmultiplier keeps track of M221 commands during the print.  Default is 0.95 as this is the default value in the
# prusa MK3 firmware.   You can change here if needed
extrusionMultiplier = 0.95

# provide extra filament at the end of the run
extraFilament = 150



#toolchange is a variable that keeps track if the processed G-Code is part of a toolchange or a regular path
# it is set based on patterns used in the gcode
ToolChange = False
FilInfo = False


# HexifyShort is used to turn a short integer into the specific notation used by Mosaic
def HexifyShort(num):
    return "D" + '{0:04x}'.format(num)

# HexifyLong is used to turn a 32-bit integer into the specific notation used by Mosaic
def HexifyLong(num):
    return "D" + '{0:08x}'.format(num)

# HexifyFloat is used to turn a 32-but floating point number into the specific notation used by Mosaic
def HexifyFloat(f):
    return "D" + (hex(struct.unpack('<I', struct.pack('<f', f))[0]))[2:]


#generate algorithm information
def Algorithms():
    global AlgorithmCount, O32Table
    for Filament_In  in range(0 , len(FilamentTransition)):
        for Filament_Out in range(0 ,len(FilamentTransition[Filament_In])):
            if FilamentTransition[Filament_In][Filament_Out]:
                  O32Table += "O32 D{}{} {} {} {}\n".format(Filament_In+1, Filament_Out+1,
                                                            FilamentHeat[Filament_In][Filament_Out],
                                                            FilamentCompression[Filament_In][Filament_Out] ,
                                                            FilamentCooling[Filament_In][Filament_Out])
                  AlgorithmCount+=1



# keep track of the filament changes and generate the corresponding O30 commands that go in the header of the file
def SwitchColor( newTool , Location):
    global O30Table, O30TableTxt,  currenttool, LastLocation, SpliceCount, SpliceOffset, FilamentUsed, Layer

    # some commands are generated at the end to unload filament, they appear as a reload of current filament - messing up things
    if newTool == currenttool:
        return

    Location += SpliceOffset

    SpliceLength = Location - LastLocation

    if (newTool == -1):
        Location += extraFilament
    else:
        FilamentUsed[newTool] = True


    if (currenttool != -1):
        O30Table += "O30 D"+ '{0:01x}'.format(currenttool)+" "+HexifyFloat(Location) + "\n"
        O30TableTxt += ";       S{:04} - {:-8.2f} -> {:-8.2f} = {:-8.2f}mm\n".format(SpliceCount,LastLocation,Location,SpliceLength)
        LastLocation = Location

        if  (newTool != -1):
            FilamentTransition[FilamentType[currenttool]-1][FilamentType[newTool]-1] = True

    SpliceCount +=1

    if SpliceCount==2:
        if SpliceLength < 100:
            O30TableTxt += ";       ERROR: Short first splice (<100mm)\n"
    elif SpliceCount>2:
        if SpliceLength < 80:
            O30TableTxt += ";       ERROR: Short splice (<80mm) Length:{} Layer:{} Tool:{}\n".format(SpliceLength, Layer, currenttool)

    currenttool = newTool


# keep track of the filaments that are used throughout the print.
# This information is stored in the header of the file
def FilamentUsage():
    result = "O25 "
    # all filament is type 1 for now, need to work on including type info in Slic3r
    for i in range(4):
        if FilamentUsed[i]:
            result +="D{}{}{} ".format(FilamentType[i], FilamentColor[i],FilamentName[i])
        else:
         result += "D0 "
    return result+"\n"

# Generate the Omega - Header that drives the plette 2 to generate filament

def OmegaHeader(Name):
    global SpliceOffset

    Algorithms()

    header = []
    header.append('O21 ' + HexifyShort(20)+"\n")  # MSF2.0
    header.append('O22 D' + PrinterProfile+"\n")  # printerprofile used in Palette2
    header.append('O23 D0001'+"\n" )              # unused
    header.append('O24 D0000'+"\n" )              # unused
    header.append(FilamentUsage())
    header.append('O26 ' + HexifyShort(SpliceCount)+"\n")
    header.append('O27 ' + HexifyShort(PingCount)+"\n")
    header.append('O28 ' + HexifyShort(AlgorithmCount)+"\n")
    header.append('O29 ' + HexifyShort(HotSwapCount)+"\n")
    #generate list of splices
    header.append (O30Table)


    header.append(O32Table)
    header.append("O1 D{} {}".format(Name,HexifyFloat(TotalExtrusion+ SpliceOffset +100))+"\n")
    header.append("M0\n")
    header.append("T0\n")

    header.append(";------------------:"+"\n")
    header.append(";SPLICE INFORMATION:"+"\n")
    header.append(";------------------:"+"\n")
    header.append(";       Splice Offset = {:-8.2f}mm\n".format(SpliceOffset))
    header.append(O30TableTxt)
    header.append("\n\n\n;------------------:"+"\n")
    header.append(";PING  INFORMATION:"+"\n")
    header.append(";------------------:"+"\n")
    header.append(PingText)
    header.append("\n;Processed by P2PP version {}\n\n".format(__version__))
    return header


# G Code parsing routine
def ParseGCodeLine(gcodeFullLine):
    global TotalExtrusion,extrusionMultiplier, Layer, PrinterProfile
    global LastPing, PingExp, PingInterval, PingCount
    global PingText, ToolChange, CurrentTool, ToolChange, FilInfo
    global SpliceOffset

    if len(gcodeFullLine)<2:
        return gcodeFullLine

    gcodeCommand2 = gcodeFullLine[0:2]
    gcodeCommand4 = gcodeFullLine[0:4]


    # Processing of extrusion multiplier commands
    #############################################
    if gcodeCommand4=="M221":
        for part in gcodeFullLine.split(" "):
            if(part==""):
                continue
            if part[0] == 'S':
                extrusionMultiplier = float(part[1:])/100

    # Processing of Extruder Movement commands
    # and generating ping at thereshold intervals
    #############################################
    if gcodeCommand2 == "G1":
        for part in gcodeFullLine.split(" "):
            if (part==""):
                continue
            if part[0] == 'E':
                offsetE = part[1:]
                TotalExtrusion += float(offsetE) * extrusionMultiplier
                if (TotalExtrusion - LastPing) > PingInterval :
                    PingInterval = PingInterval * PingExp
                    PingCount +=1
                    if PingInterval >1000:
                        PingInterval = 1000
                    gcodeFullLine = gcodeFullLine + "\n;Palette 2 - PING\nG4 S0\nO31 "+HexifyFloat(TotalExtrusion)
                    gcodeFullLine = gcodeFullLine + "\nM117 PING {:03} {:-8.2f}mm\n\n".format(PingCount , TotalExtrusion)
                    dist = TotalExtrusion - LastPing
                    LastPing = TotalExtrusion
                    PingText = PingText + ";       Ping {:04} at {:-8.2f}mm dist:{:-8.2f}mm\n".format(PingCount, TotalExtrusion, dist)



    # Process Toolchanges. Build up the O30 table with Splice info
    ##############################################################
    if gcodeFullLine[0] == 'T':
        newTool = int(gcodeFullLine[1])
        SwitchColor( newTool  , TotalExtrusion)
        FilInfo = True
        return ";P2PP removed "+gcodeFullLine

    # Build up the O32 table with Algo info
    #######################################
    if gcodeFullLine.startswith(";P2PP FT=") and FilInfo :  #filament type information
        p2ppinfo = gcodeFullLine[9:].rstrip("\n")
        try:
            FilamentType[currenttool] = FilamentTypeConversion[p2ppinfo]
        except:
             FilamentType[currenttool] = 1   #default profile = 1


    if gcodeFullLine.startswith(";P2PP FN=") and FilInfo :  #filament color information
        p2ppinfo = gcodeFullLine[9:].strip("\n-+!@#$%^&*(){}[];:\"\',.<>/?").replace(" ", "_")
        FilamentName[currenttool] = p2ppinfo
        print("{} = {}".format(currenttool, p2ppinfo))

    if gcodeFullLine.startswith(";P2PP FC=#") and FilInfo :  #filament color information
        p2ppinfo = gcodeFullLine[10:].rstrip("\n")
        FilamentColor[currenttool] = p2ppinfo



    # Other configuration information
    # this information should be defined in your Slic3r printer settings, startup GCode
    ###################################################################################
    if gcodeFullLine.startswith(";P2PP PRINTERPROFILE=") and PrinterProfile=='':   # -p takes precedence over printer defined in file
        PrinterProfile = gcodeFullLine[21:].rstrip("\n")
    if gcodeFullLine.startswith(";P2PP SPLICEOFFSET="):
        SpliceOffset = float(gcodeFullLine[19:].rstrip("\n"))


    # Next section(s) clean up the GCode generated for the MMU
    # specially the rather violent unload/reload reauired for the MMU2
    ###################################################################
    if "TOOLCHANGE START" in gcodeFullLine:
        FilInfo = False
        ToolChange = True
    if "TOOLCHANGE END" in gcodeFullLine:
        ToolChange = False

    #--------------------------------------------------------------
    # Do not perform this part of the GCode for MMU filament unload
    #--------------------------------------------------------------
    DiscardedMoves = ["E-15.0000" , "G1 E10.5000" , "G1 E3.0000" , "G1 E1.5000"]
    if ToolChange:
        if gcodeCommand2=="G1":
            for filter in DiscardedMoves:
                if filter in gcodeFullLine:
                    return ";P2PP removed "+gcodeFullLine
        if gcodeCommand4=="M907":
            return ";P2PP removed "+gcodeFullLine
        if gcodeFullLine.startswith("G4 S0"):
            return ";P2PP removed "+gcodeFullLine


    # Layer Information
    if gcodeFullLine.startswith(";LAYER "):
        Layer = gcodeFullLine[7:].strip("\n")
    # return the original line if no change required
    ################################################
    return gcodeFullLine


#########################################################
#################### MAIN ROUTINE #######################
#########################################################
def main(argv):
    global SpliceOffset, PrinterProfile, O30TableTxt, graphicalUserInterface
    fname = ""
    _taskName = "NoName"

    try:
        opts, args = getopt.getopt( argv, "gci:o:p:")
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-g":
            ##################
            #do gui stuff here
            ##################
            graphicalUserInterface = True
        if opt == "-i":
            fname = arg
            basename = os.path.basename(fname)
            _taskName = os.path.splitext(basename)[0]

        if opt == '-o':
            SpliceOffset = float(arg)
        if opt == '-p':
            PrinterProfile = arg

    OutputArray = []

    # for debugging purposes only - this allows running the tool outside of slicer
    if DEBUG_MODE:
        fname = DEBUG_MODE_INPUT_FILE

    #read the input file
    ####################
    with open(fname) as opf:
        gcode = opf.readlines()
    opf.close

    # Process the file
    ##################
    for line in gcode:
      OutputArray.append(ParseGCodeLine(line))
    SwitchColor( -1 , TotalExtrusion)
    header=OmegaHeader(_taskName)

    #write the output file
    ######################
    opf = open( fname , "w")
    opf.writelines(header)
    opf.writelines(OutputArray)

if __name__ == "__main__":
    main(sys.argv[1:])