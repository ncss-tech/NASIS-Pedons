#-------------------------------------------------------------------------------
# Name:        Import_NCSSPedonDataTextFiles_into_FGDB
# Purpose:
#
# Author:      Adolfo.Diaz
#              This tool will import NCSS pedon records from existing text files.
#              The text files were exported by Jason Nemecek.
#              The tool will take an existing empty FGDB with the correct schema
#              produced from the 'create_Schema_from_NCSS_Lab_Table_Metadata.py'
#              The tool takes in 3 parameters:
#                  1) directory path of text files
#                  2) directory where FGDB will be created
#                  3) Name of FGDB
#              The tool will error out if there is a discrepancy between the FGDB
#              schema and the import files.  The names have to match exactly.
#              There were several temporary adjustments that needed to be made:
#                  1) Webmap table was manually imported using catalog and not the script
#                  2) analyte table schemas do not match.
#
#
# Created:     14/11/2019
# Copyright:   (c) Adolfo.Diaz 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        #print msg

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

## ================================================================================================================
def createPedonFGDB():
    """This Function will create a new File Geodatabase using a pre-established XML workspace
       schema.  All Tables will be empty and should correspond to incoming text files.
       Relationships will also be pre-established.
       Return false if XML workspace document is missing OR an existing FGDB with the user-defined
       name already exists and cannot be deleted OR an unhandled error is encountered.
       Return the path to the new Pedon File Geodatabase if everything executes correctly."""

    try:
        AddMsgAndPrint("\nCreating File Geodatabase",0)
        arcpy.SetProgressorLabel("Creating File Geodatabase")

        # pedon xml template that contains empty pedon Tables and relationships
        # schema and will be copied over to the output location
        pedonXML = os.path.dirname(sys.argv[0]) + os.sep + "Create_NCSSLabDatabase_Schema_XMLWorkspace.xml"
        localPedonGDB = os.path.dirname(sys.argv[0]) + os.sep + "NCSSLabDatabase_Schema_Template.gdb"

        # Return false if pedon fGDB template is not found
        if not arcpy.Exists(localPedonGDB):
            AddMsgAndPrint("\t" + os.path.basename(localPedonGDB) + " FGDB template was not found!",2)
            return False

        newPedonFGDB = os.path.join(outputFolder,GDBname + ".gdb")

        if arcpy.Exists(newPedonFGDB):
            try:
                arcpy.Delete_management(newPedonFGDB)
                arcpy.RefreshCatalog(outputFolder)
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Deleting and re-creating FGDB\n",1)
            except:
                AddMsgAndPrint("\t" + GDBname + ".gdb already exists. Failed to delete\n",2)
                return False

        # copy template over to new location
        AddMsgAndPrint("\tCreating " + GDBname + ".gdb with NCSS Characterization Data V.XXXXX")
        arcpy.Copy_management(localPedonGDB,newPedonFGDB)

        """ ------------------------------ Code to use XML Workspace -------------------------------------------"""
##        # Return false if xml file is not found
##        if not arcpy.Exists(pedonXML):
##            AddMsgAndPrint("\t" + os.path.basename(pedonXML) + " Workspace document was not found!",2)
##            return False
##
##        # Create empty temp File Geodatabae
##        arcpy.CreateFileGDB_management(outputFolder,os.path.splitext(os.path.basename(newPedonFGDB))[0])
##
##        # set the pedon schema on the newly created temp Pedon FGDB
##        AddMsgAndPrint("\tImporting NCSS Pedon Schema 7.3 into " + GDBname + ".gdb")
##        arcpy.ImportXMLWorkspaceDocument_management(newPedonFGDB, pedonXML, "DATA", "DEFAULTS")

        arcpy.UncompressFileGeodatabaseData_management(newPedonFGDB)
        arcpy.RefreshCatalog(outputFolder)
        AddMsgAndPrint("\tSuccessfully created: " + GDBname + ".gdb")

        return newPedonFGDB

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        return False

    except:
        AddMsgAndPrint("Unhandled exception (createFGDB)", 2)
        errorMsg()
        return False

## ================================================================================================================
def importTabularData():
    """ This function will import the SSURGO .txt files from the tabular folder.
        tabularFolder is the absolute path to the tabular folder.
        tblAliases is a list of the physical name of the .txt file along with the Alias name.
        Return False if error occurs, true otherwise.  there is a list of files that will not be
        imported under "doNotImport".  If the tabular folder is empty or there are no text files
        the survey will be skipped."""

    try:
        env.workspace = pedonFGDB

        #AddMsgAndPrint("\n\tImporting Tabular Data for: " + SSA,0)

        # For each item in sorted keys
        for GDBtable in pedonFGDBTables:

            #if GDBtable != 'layer':continue
            #if GDBtable == 'analyte':continue

            # Absolute path to text file
            txtPath = os.path.join(textFilePath,GDBtable + ".txt")

            AddMsgAndPrint("\nImporting Tabular Data for: " + GDBtable,0)

            if os.path.exists(txtPath):

                # Continue if the text file contains values. Not Empty file
                if os.path.getsize(txtPath) > 0:

                    # Put all the field names in a list; used to initiate insertCursor object
                    fieldList = arcpy.Describe(GDBtable).fields
                    nameOfFields = []
                    fldLengths = list()

                    for field in fieldList:

                        # record is a LAB pedon. Addd XY token to list
                        if GDBtable == pedonFC and field == 'Shape':

                            # Pedon feature class will have X,Y geometry added; Add XY token to list
                            nameOfFields.append('SHAPE@XY')
                            fldLengths.append(0)  # X coord
                            fldLengths.append(0)  # Y coord
                            continue

                        if field.type != "OID":
                            nameOfFields.append(field.name)
                            if field.type.lower() == "string":
                                fldLengths.append(field.length)
                            else:
                                fldLengths.append(0)

                    del fieldList, field
                    #print "------------------- Number of fields: " + str(len(nameOfFields))
                    #print nameOfFields

                    # The csv file might contain very huge fields, therefore increase the field_size_limit:
                    # Exception thrown with IL177 in legend.txt.  Not sure why, only 1 record was present
                    try:
                        csv.field_size_limit(sys.maxsize)
                    except:
                        csv.field_size_limit(sys.maxint)

                    # Number of records in the SSURGO text file
                    textFileRecords = sum(1 for row in csv.reader(open(txtPath, 'rb'), delimiter='|', quotechar='"'))

                    # Initiate Cursor to add rows
                    cursor = arcpy.da.InsertCursor(GDBtable,nameOfFields)

                    # counter for number of records successfully added; used for reporting
                    numOfRowsAdded = 0
                    reader = csv.reader(open(txtPath, 'rb'), delimiter='|', quotechar='"')

                    # Strictly for headers
                    i = 1
                    headerRow = ""

                    try:
                        # Return a reader object which will iterate over lines in txtPath
                        for rowInFile in reader:

                            # Skip first record if text files contain headers
                            if fileContainHeaders and i==1:
                               i+=1
                               headerRow = rowInFile
                               continue

                            # This is strictly temporary bc the 'combine_nasis_ncss' txt
                            # file containes duplicate sets of records
                            if GDBtable == pedonFC:
                               if rowInFile == headerRow:
                                  print "Duplicate records start"
                                  break

                            """ Cannot use this snippet of code b/c some values have exceeded their field lengths; need to truncate"""
                            # replace all blank values with 'None' so that the values are properly inserted
                            # into integer values otherwise insertRow fails
                            # newRow = [None if value =='' else value for value in rowInFile]

                            newRow = list()  # list containing the values that make up a specific row
                            fldNo = 0        # list position to reference the field lengths in order to compare

                            for value in rowInFile:
                                fldLen = fldLengths[fldNo]

                                if value == '':
                                    value = None

                                elif fldLen > 0:
                                    value = value[0:fldLen]

                                if value != None and value.startswith(" "):
                                    value = value[1:len(value)]

                                # There were issues with values containing non-ASCII characters.
                                # Substitute non-ASCII characters with spaces.
                                if value != None:
                                    try:
                                        value.encode('utf-8')
                                    except:
                                        value = re.sub(r'[^\x00-\x7F]+',' ', value)

                                newRow.append(value)
                                fldNo += 1

                            # Add XY coordinates to the pedon point feature class.
                            if GDBtable == pedonFC:
                                try:
                                    xValue = float(newRow[66])  # Long
                                    yValue = float(newRow[65])  # Lat
                                except:
                                    xValue = 0.00
                                    yValue = 90.0

                                newRow.insert(nameOfFields.index('Shape'),(xValue,yValue))
                                del xValue,yValue

                            cursor.insertRow(newRow)
                            numOfRowsAdded += 1

                            del newRow, rowInFile

                    except:
                        AddMsgAndPrint("\n\t\tError inserting record in table: " + GDBtable,2)
                        AddMsgAndPrint("\t\t\tRecord # " + str(numOfRowsAdded + 1),2)
                        AddMsgAndPrint("\t\t\tValue: " + str(newRow),2)
                        AddMsgAndPrint("\t\t\t-------------------------")
                        AddMsgAndPrint("\t\t\tOrig: " + str(rowInFile))
                        AddMsgAndPrint("\t\t\tField Number: " + str(fldNo))
                        errorMsg();exit()
                        continue

                    del cursor

                    #AddMsgAndPrint("\t\t--> " + iefileName + theAlias + theRecLength + " Records Added: " + str(splitThousands(numOfRowsAdded)),0)
                    AddMsgAndPrint("\t\t--> " + GDBtable + ": Records Added: " + str(splitThousands(numOfRowsAdded)),0)

                    # Add the header row to the number of rows added.
                    if fileContainHeaders: numOfRowsAdded+=1

                    # compare the # of rows inserted with the number of valid rows in the text file.
                    if numOfRowsAdded != textFileRecords:
                        AddMsgAndPrint("\t\t\t Incorrect # of records inserted into: " + GDBtable, 2 )
                        AddMsgAndPrint("\t\t\t\t TextFile records: " + str(splitThousands(textFileRecords)),2)
                        AddMsgAndPrint("\t\t\t\t Records Inserted: " + str(splitThousands(numOfRowsAdded)),2)

                else:
                    AddMsgAndPrint("\t\t--> " + GDBtable + ": Records Added: 0",0)

            else:
                AddMsgAndPrint("\t\t--> " + GDBtable + ".txt does NOT exist.....SKIPPING ",2)

            arcpy.SetProgressorPosition()

        # Resets the progressor back to is initial state
        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel(" ")

        return True

    except arcpy.ExecuteError:
        AddMsgAndPrint(arcpy.GetMessages(2),2)
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + GDBtable,2)
        return False

    except csv.Error, e:
        AddMsgAndPrint('\nfile %s, line %d: %s' % (txtPath, reader.line_num, e))
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + GDBtable,2)
        errorMsg()
        return False

    except IOError as (errno, strerror):
        AddMsgAndPrint("\nI/O error({0}): {1}".format(errno, strerror) + " File: " + txtPath + "\n",2)
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + GDBtable,2)
        errorMsg()
        return False

    except:
        AddMsgAndPrint("\nUnhandled exception (importTabularData) \n", 2)
        AddMsgAndPrint("\tImporting Tabular Data Failed for: " + GDBtable,2)
        errorMsg()
        return False



# =========================================== Main Body ==========================================
# Import modules
import sys, string, os, traceback, re, arcpy, time, csv
from arcpy import env
from sys import getsizeof, stderr
from itertools import chain
from collections import deque

if __name__ == '__main__':

    try:

        textFilePath = arcpy.GetParameter(0)
        outputFolder = arcpy.GetParameterAsText(1)
        GDBname = arcpy.GetParameterAsText(1)

        textFilePath = r'N:\flex\Dylan\NCSS_Characterization_Database\Updated_Schema_2019\NCSS_LabData_export'
        outputFolder = r'O:\Temp'
        GDBname = 'NCSS_Characterization_Database_newSchema.gdb'

        pedonFC = 'combine_nasis_ncss'     # name of FC that contains the Lat,Long and will be afeature class

        # Boolean indicating input text files have headers to skip
        fileContainHeaders = True

        # Step 1 - Create List of .txt files
        textFileList = [file.replace('.txt','') for file in os.listdir(textFilePath) if file.endswith('.txt')]

        # Step 2 - Create FGDB
        """ ------------------------------------------------------Create New File Geodatabaes and get Table Aliases for printing -------------------------------------------------------------------
        Create a new FGDB using a pre-established XML workspace schema.  All tables will be empty
        and relationships established.  A dictionary of empty lists will be created as a placeholder
        for the values from the XML report.  The name and quantity of lists will be the same as the FGDB"""

        pedonFGDB = createPedonFGDB()
        #pedonFGDB = r'N:\flex\Dylan\NCSS_Characterization_Database\Updated_Schema_2019\NCSS_Characterization_Database_newSchema.gdb'
        arcpy.env.workspace = pedonFGDB

        if not pedonFGDB:
            AddMsgAndPrint("\nFailed to Initiate Empty Pedon File Geodatabase.  Error in createPedonFGDB() function. Exiting!",2)
            exit()

        # Step 3 - Compare names of text files to tables in FGDB
        pedonFGDBTables = arcpy.ListTables("*")
        for fcs in arcpy.ListFeatureClasses('*'):
            pedonFGDBTables.append(fcs)

        discrepancy = list(set(pedonFGDBTables) - set(textFileList))

        if len(discrepancy) > 0:
           AddMsgAndPrint("\nThere are " + str(len(discrepancy)) + " discrepancies between the FGDB and text files",2)
           for item in discrepancy:
               if item in pedonFGDBTables:
                  AddMsgAndPrint("\t\"" + item + "\" Table does not have a corresponding text file")
               else:
                  AddMsgAndPrint("\t\"" + item + "\" text file does not have a corresponding FGDB Table")
           AddMsgAndPrint("\nAll discrepancies must be addressed before continuing.....EXITING!")
           exit()

        importTabularData()



    except MemoryError:
        AddMsgAndPrint("\n\nOut of Memory Genius! --- " + str(sys.getsizeof(pedonGDBtables)),2)
        exit()

    except:
        errorMsg()




















