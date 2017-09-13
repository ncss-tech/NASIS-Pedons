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

## ================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ===================================================================================
def convertTablesToCSV(GDB):

    try:
        env.workspace = GDB
        tablesToConvert = [table for table in arcpy.ListTables()]

        for fc in arcpy.ListFeatureClasses():
            tablesToConvert.append(fc)

        if len(tablesToConvert):

            for table in tablesToConvert:

                #if not table == 'phtext':continue

                numOfRows = int(arcpy.GetCount_management(table).getOutput(0))
                fieldNames = [f.name for f in arcpy.ListFields(table)]

                tempTable = table + "Temp.csv"
                permTable = outputFolder + os.sep + table + ".csv"

                if arcpy.Exists(outputFolder + os.sep + tempTable):
                    arcpy.Delete_management(outputFolder + os.sep + tempTable)

                if arcpy.Exists(permTable):
                    continue
                    #arcpy.Delete_management(permTable)

                AddMsgAndPrint("Converting " + table + " to CSV file.  Num of records: " + splitThousands(numOfRows))
                arcpy.TableToTable_conversion(table,outputFolder,tempTable)

                # file needs to be opened in Universal mode otherwise an error is thrown:
                # new-line character seen in unquoted field - do you need to open the file in universal-newline mode
                with open(outputFolder + os.sep + tempTable,'rU') as csvFile:
                    #csvReader = csv.reader(open(csvFile, 'rU'), dialect=csv.excel_tab)
                    csvReader = csv.reader(csvFile)
                    with open(permTable,"wb") as csvResult:
                        csvWrite = csv.writer(csvResult,delimiter='|',quotechar='"')
                        for row in csvReader:
                            csvWrite.writerow(row[1:])

                arcpy.Delete_management(outputFolder + os.sep + tempTable)

    except:
        errorMsg()
        AddMsgAndPrint("\nUnable to get table information from: " + GDB,2)
        exit()


# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy,csv
from arcpy import env

if __name__ == '__main__':

    inputGDB = arcpy.GetParameter(0)
    outputFolder = arcpy.GetParameterAsText(1)

    inputGDB = r'E:\All_Pedons\NCSS_Characterization_Database\NCSS_Soil_Characterization_Database_FGDB_20170517.gdb'
    outputFolder = r'E:\All_Pedons\NCSS_Characterization_Database\CSV_files'

    convertTablesToCSV(inputGDB)
