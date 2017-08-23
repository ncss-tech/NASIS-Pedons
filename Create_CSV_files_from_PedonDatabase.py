#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     22/08/2017
# Copyright:   (c) Adolfo.Diaz 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print msg

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError("\n" + msg)

    except:
        pass

## ===================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def getListOfTables(GDB):

    try:
        tableDict = dict()
        env.workspace = GDB

        for table in arcpy.ListTables():

            if not tableDict.has_key(table):

                numOfRows = int(arcpy.GetCount_management(table).getOutput(0))
                numOfFields = 0
                fmObject = arcpy.FieldMappings()

                #Populate field object to remove OID field
                for field in arcpy.ListFields(table):
                    if not field.type == "OID" and not field.type == "Geometry":
                        fmObject.addFieldMap(field.name)
                        numOfFields += 1

                tableDict[table] = (len(table),table + ".csv",numOfRows,fmObject,numOfFields)

        if not len(tableDict):
            AddMsgAndPrint("\nCould not get table info from " + GDB,2)
            exit()

    except:
        AddMsgAndPrint("\nUnable to get table information from: " + GDB,2)
        exit()


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy
from arcpy import env

if __name__ == '__main__':

    inputGDB = arcpy.GetParameter(0)
    outputFolder = arcpy.GetParameterAsText(1)

    tablesToConvert = getListOfTables(inputGDB)
