#!/usr/bin/python
#
#    PyMPG - Python Mileage Processing GUI
#
# Ryan Helinski


import sys
import csv
import time
import datetime
#import traceback
import subprocess
import os
import configparser
import xml.etree.ElementTree as etree
from xml.dom import minidom

import gi; gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GdkPixbuf

# Global settings
progname = "PyMPG"
progver = "2.2"
progcopy = "Copyright Ryan Helinski"
progcomm = "A simple tool for keeping track of gas mileage implemented in Python using PyGTK."
progurl = "http://pgmdb.sf.net/"
pmxversion = '0.2'

invalidStr = "--"
dateFmtStr = "%Y/%m/%d"

daysPerYear = 365.25
numSigFigs = 3

pumpxpm = sys.path[0] + "/pump.png"
try:
    pumppb = GdkPixbuf.Pixbuf.new_from_file(pumpxpm)
except GLib.GError as error:
    print(error)

def mktimestamp(timeobj):
    return int(time.mktime(timeobj.timetuple()))

def fmttimestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime(dateFmtStr)

def etree_pretty(elem):
    '''Return a pretty-printed XML string for the Element.
    '''
    rough_string = etree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='\t')

# TODO most of these should move to the record class
storedFields = ['odo', 'date', 'gals', 'dpg', 'station', 'address', 'city', 'state', 'zip', 'fill', 'comment']
storedFieldLabels = ['Odometer', 'Date', 'Gallons', 'Price / Gal', 'Station', 'Address', 'City', 'State', 'ZIP', 'Filled?', 'Comment']

fullFields = ['odo', 'date', 'days', 'dist', 'gals', 'mpg', 'dpg', 'tankcost', 'mpd', 'dpd', 'dpm', 'station', 'address', 'city', 'state', 'zip', 'fill', 'comment']
columnNames = ['Odo.', 'Date', 'Days', 'Dist.', 'Gals', 'mi/gal', '$/gal', 'Cost', 'mi/day', '$/day', '$/mi', 'Station', 'Address', 'City', 'State', 'ZIP', 'Fill?', 'Comment']

numFields = ['odo', 'date', 'days', 'dist', 'gals', 'mpg', 'dpg', 'tankcost', 'mpd', 'dpd', 'dpm']

# columns to put into waveform
wfmcols = ['date', 'days', 'odo', 'dist', 'gals', 'dpg', 'tankcost', 'mpd', 'mpg']

sortField = storedFields.index('odo')

class UserPrefManager:
    'Load and save user preferences'

    file_path = os.path.expanduser(os.path.join('~', '.pympg', 'pympg.ini'))

    def __init__(self):
        self.config = configparser.ConfigParser()
        if (os.path.isfile(self.file_path)):
            self.load()
        else:
            self.load_defaults()

    def __del__(self):
        self.save()

    def load(self):
        self.config.read(self.file_path)

    def load_defaults(self):
        self.config['gnuplot'] = defaults = {'path': 'gnuplot',
                                             'term': ''}
        self.config['recent'] = []

    def save(self):
        with open(self.file_path, 'w') as configfile:
            self.config.write(configfile)


# TODO these should be part of the database, but they are not
VehProperties = dict()
vehPrefFields = ["Year","Make","Model","TankSize","ServiceOffset","ServiceInterval","Owner"]

class FuelRecord():

    def __init__(self, source=None):
        self.fields = dict()

        if (type(source) is None):
            None
        elif (type(source) == list):
            self.fromlist(source)
        elif (type(source) == dict):
            self.fromdict(source)

    def __contains__(self, name):
        return name in self.fields.keys()

    def __getattr__(self, name): # object.name, return raw data
        return self.fields[name]

    def __setitem__(self, name, value):
        self.fields[name] = value

    def __repr__(self): # string representation
        return str(self.fields)

    def __getitem__(self, key): # object[name], format a string
        return self.getText(key)

    def __cmp__(a, b):
        return cmp(a.odo, b.odo)

    def __lt__(a, b):
        return a.odo < b.odo

    def fromlist(self, row):
        if (len(row) != len(storedFields)):
            raise NameError('Wrong number of fields in CSV file!')

        for field, index in storedFields.pairs():
            self.fields[field] = self.formatText(field, row[index])

    def fromdict(self, mydict):
        for field in storedFields:
            try:
                self.fields[field] = self.formatText(field, mydict[field])
            except KeyError:
                # Could use a getDefault() method
                self.fields[field] = (False if (field == 'fill') else "")
            except Exception as e:
                raise Exception('%s at odo %s' % (str(e), mydict['odo']))

    def tolist(self):
        j = 0
        textrow = []
        for j in range(0, len(storedFields)):
            textrow.append(self.getText(storedFields[j]))
        return textrow

    def todict(self):
        j = 0
        attribs = dict()
        for j in range(0, len(storedFields)):
            attribs[storedFields[j]] = self.getText(storedFields[j])
        return attribs

    def getText(self, field):
        if (field == "date"):
            return self.fields[field].date().strftime(dateFmtStr)

        elif (field == "tankcost"):
            cost = self.fields['gals'] * self.fields['dpg']
            return "%.2f" % cost

# TODO justify numeric fields to right
        elif (field == "fill"):
            return "Yes" if self.fields[field] else "No"

        # no special treatment necessary, return as-is
        else:
            return "%s" % self.fields[field]

    def setText(self, field, text):
        self.fields[field] = self.formatText(field, text)

    @staticmethod
    def formatText(field, text):
        try:
            if (field == "odo"):
                retval = int(text)
            elif (field == "date"):
                retval = datetime.datetime.strptime(text, dateFmtStr)
            elif (field == "gals" or field == "dpg"):
                retval = round(float(text), numSigFigs)
            elif (field == "fill"):
                retval = (text.lower() == "yes")
            else:    # return value as-is
                retval = text.strip()
        except Exception as e:
            raise Exception('%s in field "%s" with value "%s"' % (str(e), field, text))

        return retval

class Address:
    def __init__(self, address="", city="", state="", zip=0):
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip


# This class opens/saves files, and manages the data in memory
class DataBase:
    # variables here are static
    dirty_bit = False        # true if the data from the file has been modified
    filename = ""         # name of the file that's open
    recordTable = []        # the actual records
    addressTable = []         # addresses of stations

    def __getitem__(self, index):
        """
        This enables you to get a record from the database without
        using the recordTable directly.
        i.e., myDB.recordTable[index] -> myDB[index]
        """
        return self.recordTable[index]

        def __delitem__ (self, item):
                del self.recordTable[item]

    def __len__(self):
        return len(self.recordTable)

    def newfile(self):
        self.recordTable = []
        self.filename = ""

        return

    def loadFile(self, filename):
        # Load records from CSV file
        self.newfile()

        if (filename.lower().endswith('csv')):
            fileReader = csv.reader(open(filename), delimiter=',', quotechar='"')

            for row in fileReader:
                # check first if this is a preference record
                if (row[0] == 'pref'):
                    print("WARNING: Ignoring user preference from vehicle data file")

                elif (row[0] == 'veh'):
                    VehProperties[row[1]] = row[2]

                else:
                    self.recordTable.append(FuelRecord(row))

        elif (filename.lower().endswith('xml')):
            mytree = etree.parse(filename)
            myroot = mytree.getroot()

            for child in myroot[0]:
                if (child.tag == 'user'):
                    print("WARNING: Ignoring user preference from vehicle data file")
                if (child.tag == 'vehicle'):
                    for pref in child:
                        VehProperties[pref.attrib['name']] = pref.attrib['value']
                if (child.tag == 'fuel'):
                    for record in child:
                        # For backwards-compatibility
                        if (myroot[0].attrib['version'] == '0.1' and 'location' in record.attrib):
                            record.attrib['address'] = record.attrib['location']
                            del record.attrib['location']
                        self.recordTable.append(FuelRecord(record.attrib))

        else:
            raise NameError("Unknown file type")

        self.filename = filename # Save file name for later
        self.addRecent()

        self.sortRecords()

        return

    def saveCSVFile(self):
        'Save records back to a CSV file'

        fileWriter = csv.writer(open(self.filename, 'w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

        for prop in VehProperties.keys():
            fileWriter.writerow(['veh', prop, VehProperties[prop]])

        i = 0
        for i in range(0, len(self.recordTable)):
            fileWriter.writerow(self[i].tolist())

    def saveXMLFile(self):
        'Create an XML'

        myxml = etree.Element('xml', attrib={'version': '1.0', 'encoding': 'UTF-8'})
        mypmx = etree.SubElement(myxml, 'pmx', attrib={'version': pmxversion, 'generator': progname})

        myveh = etree.SubElement(mypmx, 'vehicle')
        for prop in VehProperties.keys():
            etree.SubElement(myveh, 'prop', attrib={'name' : prop, 'value' : VehProperties[prop]})

        myfuel = etree.SubElement(mypmx, 'fuel')

        i = 0
        for i in range(0, len(self.recordTable)):
            etree.SubElement(myfuel, 'record', attrib=self[i].todict())

        with open(self.filename, 'w') as xmlfile:
            xmlfile.write(etree_pretty(myxml))

    def addRecent(self):
        if 'recent' not in UserPrefs.config:
            UserPrefs.config['recent'] = {}
        UserPrefs.config['recent']['slot0'] = self.filename


    def saveFile(self):
        basename, extension = os.path.splitext(self.filename)
        if not extension:
            self.filename += '.xml'

        if (self.filename.lower().endswith('csv')):
            self.saveCSVFile()
        elif (self.filename.lower().endswith('xml')):
            self.saveXMLFile()
        else:
            raise NameError('Unknown file type for "%s"' % self.filename)

        self.addRecent()

        return

    def sumWhileFalse(self, row, sumfield, checkfield):
        # Start by adding this row's value
        total = float( self.getText(row, sumfield) )
        # Start with the previous row
        lastTrue = row - 1

        while (lastTrue > 1 and self.getText(lastTrue, checkfield) != "Yes"):

            try:
                total = total + float( self.getText(lastTrue, sumfield) )
            except ValueError as e:
                break
            #if sumfield == 'gals':
                #print row, lastTrue, checkfield, sumfield, self.getText(row - lastTrue, checkfield), self.getText(row - lastTrue, sumfield), total
            lastTrue -= 1 # keep going back until we find one that is true

        #print [self.getText(row, "odo"), row, lastTrue, sumfield, checkfield, total]

        return [lastTrue, total]

    def getText(self, row, field):
        # hooks for certain derived fields
        if (field == "days"):
            if (row == 0):
                return invalidStr

            timedelta = self[row].date - self[row - 1].date

            return "%d" % timedelta.days

        elif (field == "dist"):
            if (row == 0):
                return invalidStr

            return "%d" % (self[row].odo - self[row - 1].odo)

        elif (field == "mpd"):
            if (row == 0):
                return invalidStr

            dist = self[row].odo - self[row - 1].odo
            timedelta = self[row].date - self[row - 1].date
            days = timedelta.days

            # This saturates to "miles per fill-up" in the case of more than one
            # fill-up per day.
            if (days == 0):
                # I'll use the following assumption: No more than two fill-ups per day.
                # Then, in the case of the second, a half-day has passed.
                mpd = 2 * dist
            else:
                mpd = dist / days

            return "%d" % mpd

        elif (field == "mpg"):
            if (row == 0 or not self[row].fill):
                # no MPG for this record
                return invalidStr
            else:
                totalMiles = self.sumWhileFalse(row, "dist", "fill")[1]
                totalFuel = self.sumWhileFalse(row, "gals", "fill")[1]

                return "%0.1f" % (totalMiles / totalFuel)
                # DEBUG
                #return "%d %0.1f/%0.1f=%0.1f" % (row, totalMiles, totalFuel, totalMiles/totalFuel)

        elif (field == "dpd"):
            if (row == 0):
                return invalidStr

            try:
                # recursive calls here
                tankcost = float( self.getText(row, "tankcost") )
                days = float( self.getText(row, "days") )

                # dollars / day = tankcost / days
                return "%0.2f" % (tankcost / days)

            except ValueError:
                return invalidStr

            except ZeroDivisionError:
                return invalidStr

        elif (field == "dpm"):
            # dollars per mile

            if (row == 0 or not self[row].fill):
            # if did not fill, then tankcost does not correspond to distance
                return invalidStr

            try:
                tankcost = self.sumWhileFalse(row, "tankcost", "fill")[1]
                dist = self.sumWhileFalse(row, "dist", "fill")[1]

                # [tank cost] / [miles traveled]
                return "%0.3f" % (tankcost / dist)

            except ValueError:
                return invalidStr

            except ZeroDivisionError:
                return invalidStr

        # it's just a stored field
        else:
            return self[row].getText(field)

    def getRowOf(self, key):
        for x in range(0, len(self.recordTable)):
            if (key == self[x][storedFields[sortField]]):
                return x

        return False

    def addNewRecord(self, record=FuelRecord):
        #record.append(len(self.recordTable))
        self.recordTable.append(record)
        self.sortRecords()

        return

    def sortRecords(self):
        return self.recordTable.sort()

    def updateAddressBook(self):
        """Create a map from station names to addresses"""
        self.addressTable = dict()
        for record in self.recordTable:
            if (record.station == ""):
                continue
            elif (record.station not in self.addressTable.keys()):
                self.addressTable[record.station] = Address(record.address, record.city, record.state, record.zip)
            else:
                # TODO replace this copying with an Address class method
                for addressField in ['address', 'city', 'state', 'zip']:
                    if ((self.addressTable[record.station].__dict__[addressField] == "") and (addressField in record)):
                        self.addressTable[record.station].__dict__[addressField] = record[addressField]

    def deleteRecord(self, row):
        del(self[row])
        return

    # TODO broken
    def exportWaveform(self, filename):
        waveform = self.createWaveform()
        wfmfile = open(filename, 'w')
        wfmfile.write(waveform)
        wfmfile.close()

        return

    def createWaveform(self):
        # Need a function here for later piping with GNUPLOT
        # Write a header comment to label the columns
        wfm = "# "
        for x in range(0, len(self.fullFields)):
            if (not self.fullFields[x] in wfmcols):
                pass
            elif (self.fullFields[x] == 'date'):
                # Because the date field is particularly wide
                wfm += self.columnNames[x] + "\t\t"
            else:
                wfm += self.columnNames[x] + "\t"
        wfm += "\n"

        # Write data
        for x in range(0, len(self.recordTable)):
            line = ''
            # TODO could leave these points in the waveform for mi/day and $/gal
            for y in range(0, len(self.fullFields)):
                if (self.fullFields[y] == 'date'):
                    # Convert the datetime obj to Epoch seconds
                    line += "%d" % time.mktime(self[x][storedFields.index('date')].timetuple())
                elif (not self.fullFields[y] in wfmcols):
                    # Skip these, they're not useful for plotting
                    pass
                else:
                    line += "\t" + self[x].getText(self.fullFields[y])

            # Make certain sequences GNUPLOT-friendly
            line = line.replace('*', '')
            line = line.replace(invalidStr, '0')
            wfm += line + "\n"

        return wfm

    def getCol(self, field):
        col = []
        # TODO why can't I say: for item in self.recordTable ?
        for i in range(0, len(self.recordTable)):
            col.append(self[i][field])

        return col

    def getColSum(self, field):
        sum = 0
        for i in range(0, len(self.recordTable)):
            sum += float(self[i][field])

        return sum

    def getColProdSum(self, field1, field2):
        sum = 0
        for i in range(0, len(self.recordTable)):
            sum += float(self[i][field1]) * float(self[i][field2])

        return sum

    def getIndexOfDate(self, date):
        index = len(self.recordTable) - 1
        while (self[index].date > date):
            index = index - 1
        return index


    def getSummaryTable(self):
        totalGals = self.getColSum('gals')
        totalMiles = self[-1].odo - self[0].odo
        averageRange = totalMiles / len(self.recordTable)
        totalDays = (self[-1].date - self[0].date).days
        totalCost = self.getColProdSum('gals', 'dpg')
        averageMPG = totalMiles / totalGals
        averageMPY = daysPerYear * totalMiles / totalDays
        timeDiff = datetime.timedelta(days= -daysPerYear)

        indexOfYearAgo = self.getIndexOfDate(self[-1].date + timeDiff)
        milesThisYear = self[-1].odo - self[indexOfYearAgo].odo
        runningMPY = milesThisYear

        tableLabels = ['Number of records:', len(self.recordTable), '',
            'Gallons consumed:', "%.1f" % totalGals, 'gal',
            'Miles travelled:', "%d" % totalMiles, 'mi',
            'Days on record:', "%d" % totalDays, 'days',
            'Total gas cost:', "%.2f" % totalCost, 'USD',
            'Average miles/gal:', "%.2f" % averageMPG, 'mi/gal',
            'Average miles/year:', "%d" % averageMPY, 'mi',
            'Running miles/year:', "%d" % runningMPY, 'mi',
            'Average Range:', "%.2f" % averageRange, 'mi',
            ]

        if ('TankSize' in VehProperties and len(VehProperties['TankSize']) > 0):
            tableLabels.extend(['Theoretical Max. Range', "%.2f" % (averageMPG * float(VehProperties['TankSize'])), 'mi' ])

        return tableLabels

class EditWindow:

    def __init__(self, interface, database, row):
        self.interface = interface
        self.database = database
        self.row = row

    def show_error (self, string):
        md = Gtk.MessageDialog(None,
            Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.CLOSE, string)
        md.run()
        md.destroy()

    def addToRow(self, widget, offset):
        newrow = self.row + offset
        if ((newrow >= 0) and (newrow < len(self.database))):
           self.row = newrow

        self.prev_button.set_sensitive((self.row - 1) >= 0)
        self.next_button.set_sensitive((self.row + 1) < len(self.database))

        self.update()

    def update(self):

        for key, entry in self.entryMap.items():
            if (key == 'fill'):
                entry.set_active(self.database[self.row].fill)
            else:
                entry.set_text(self.database.getText(self.row, key))

        self.setWindowTitle()
        self.interface.selectRow(self.row)

        return

    def updateBool(self, entry, window, col):
        if (self.row != None):
            self.interface.updateField(entry, window, col)


    def updateField(self, entry, editwindow, col):
        if (self.row != None):
            self.interface.updateField(entry, editwindow, col)
        if (col == storedFields.index('station')):
            self.database.updateAddressBook() # TODO might not be best placed here
        if (entry.get_text() in self.database.addressTable):
        # Update the address, city, state and zip
            for addressField in ['address', 'city', 'state', 'zip']:
                if (editwindow.entryMap[addressField].get_text() == ""):
                    text = self.database.addressTable[entry.get_text()].__dict__[addressField]
                    self.entryMap[addressField].set_text(text)
                    if (self.row != None):
                        self.database[self.row][addressField] = text

    def saveNewRecord(self, widget):
        newrownum = len(self.database.recordTable)
        newrow = dict()

        try:
            for x in range(0, len(storedFields)):
                if (storedFields[x] == 'fill'):
                    newrow[storedFields[x]] = "Yes" if self.entryMap[storedFields[x]].get_active() else "No"
                else:
                    if (storedFields[x] in ['odo', 'gals', 'dpg']
                        and self.entryMap[storedFields[x]].get_text() == ""):
                        raise NameError('Missing required field')
                    newrow[storedFields[x]] = self.entryMap[storedFields[x]].get_text()

            # want to do a check here for the date being wrong
            # records are sorted by odometer, need to make sure this record isn't before the previous or after the next
        except ValueError:
            self.show_error('Invalid format, try again.')
        except NameError:
            self.show_error('You left a required field blank.')
        else:

            # If entries OK
            self.interface.makeDirty()
            self.database.addNewRecord(FuelRecord(newrow))
            self.interface.updateList()
            self.interface.updatePlot()
            self.interface.newstatus("New record created.")
            self.editwindow.destroy()

        return

    def open(self):
        self.editwindow = Gtk.Window()

        self.table = Gtk.Table(len(storedFields) + 1, 2, False)
        self.entryMap = dict()
        for x in range(0, len(storedFields)):
            label = Gtk.Label(storedFieldLabels[x])
            self.table.attach(label, 0, 1, x, x + 1)

            if (storedFields[x] == 'fill'):
                button = Gtk.CheckButton(storedFieldLabels[x])
                if (self.row is None):
                    button.set_active(False)
                else:
                    button.set_active(self.database[self.row].fill)
                button.connect("clicked", self.updateBool, self, x)
                self.table.attach(button, 1, 2, x, x + 1)
                self.entryMap[storedFields[x]] = button
            else:
                entry = Gtk.Entry()
                if (self.row is None):
                    if (storedFields[x] == 'date'):
                        entry.set_text(datetime.date.today().strftime(dateFmtStr))
                else:
                    entry.set_text(self.database.getText(self.row, storedFields[x]))
                entry.connect("activate", self.updateField, self, x)
                entry.connect("focus-out-event", self.editWindowEntryFocusOut, self, x)

                if (storedFields[x] not in ['gals', 'odo', 'date', 'dpg']):
                    # Auto-completion
                    completion = Gtk.EntryCompletion()
                    liststore = Gtk.ListStore(str)
                    entry.set_completion(completion)
                    completion.set_model(liststore)
                    completion.set_text_column(0)

                    column = self.database.getCol(storedFields[x])
                    column = set(column)
                    for item in column:
                        liststore.append([item])

                self.table.attach(entry, 1, 2, x, x + 1)
                self.entryMap[storedFields[x]] = entry

        bbox = Gtk.HButtonBox()
        if (self.row is None):
            save_button = Gtk.Button(label="Save", stock=Gtk.STOCK_OK)
            save_button.connect("activate", self.saveNewRecord)
            save_button.connect("clicked", self.saveNewRecord)
            bbox.add(save_button)
            canc_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
            canc_button.connect("activate", self.close)
            canc_button.connect("clicked", self.close) # TODO FIXME this doesn't work: TypeError: destroy() takes no arguments (1 given)
            bbox.add(canc_button)
        else:
            self.prev_button = Gtk.Button(label="Previous", stock=Gtk.STOCK_GO_BACK)
            self.prev_button.connect("activate", self.addToRow, -1)
            self.prev_button.connect("clicked", self.addToRow, -1)
            bbox.add(self.prev_button)
            self.next_button = Gtk.Button(label="Next", stock=Gtk.STOCK_GO_FORWARD)
            self.next_button.connect("activate", self.addToRow, 1)
            self.next_button.connect("clicked", self.addToRow, 1)
            bbox.add(self.next_button)
        bbox.set_spacing(20)
        bbox.set_layout(Gtk.ButtonBoxStyle.SPREAD)

        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(self.table, False, False, 0)
        vbox.pack_end(bbox, False, False, 0)
        self.editwindow.add(vbox)

        self.setWindowTitle()

        self.editwindow.show_all()

    def setWindowTitle(self):
        if (self.row is None):
            self.editwindow.set_title("New Record")
        else:
            self.editwindow.set_title("Edit Record %d" % (self.row + 1))
        return

    def editWindowEntryFocusOut(self, widget, event, editwindow, col):
        # this basically throws out the 'event'
        return self.updateField(widget, editwindow, col)

    def close(self, widget):
        self.editwindow.destroy()


# This class serves as an interface between other classes and the GTK user interface
class PyMPG:
    'Manages the GTK interface for the program'

    database = DataBase()   # a file interface class
    gnuplot_p = False        # not false if a pipe to GNUPLOT is open
    plot_type = ""        # type of plot that has been generated: 'mpd', 'mpg', or 'dpg'
    gnuplot_annot = ""        # extra string to add to GNUPLOT 'plot' command for annotating a graph
    timeScale = "all"

    def __init__(self, dname=None):

        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_title(progname)
        self.window.set_size_request(800, 600)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        try:
            self.window.set_icon(pumppb)
        except NameError as error:
            print(error)

        # Menu bar
        mb = Gtk.MenuBar()
        # File menu
        filemenu = Gtk.Menu()
        filem = Gtk.MenuItem("_File")
        filem.set_submenu(filemenu)

        agr = Gtk.AccelGroup()
        self.window.add_accel_group(agr)

        newi = Gtk.ImageMenuItem(Gtk.STOCK_NEW, agr)
        key, mod = Gtk.accelerator_parse("<Control>n")
        newi.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
        newi.connect("activate", self.menuFileNew)
        filemenu.append(newi)

        openm = Gtk.ImageMenuItem(Gtk.STOCK_OPEN, agr)
        key, mod = Gtk.accelerator_parse("<Control>o")
        openm.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
        openm.connect("activate", self.menuOpenFile)
        filemenu.append(openm)

        self.savem = Gtk.ImageMenuItem(Gtk.STOCK_SAVE, agr)
        key, mod = Gtk.accelerator_parse("<Control>s")
        self.savem.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
        self.savem.set_sensitive(False)
        self.savem.connect("activate", self.menuFileSave)
        filemenu.append(self.savem)

        self.saveasm = Gtk.ImageMenuItem(Gtk.STOCK_SAVE_AS, agr)
        self.saveasm.set_sensitive(False)
        self.saveasm.connect("activate", self.menuFileSaveAs)
        filemenu.append(self.saveasm)

        sep = Gtk.SeparatorMenuItem()
        filemenu.append(sep)

        self.propm = Gtk.MenuItem("Properties")
        self.propm.set_sensitive(False)
        self.propm.connect("activate", self.menuFileProperties)
        filemenu.append(self.propm)

        sep = Gtk.SeparatorMenuItem()
        filemenu.append(sep)

        self.exportm = Gtk.MenuItem("Export Waveform")
        self.exportm.set_sensitive(False)
        self.exportm.connect("activate", self.menuFileExport)
        filemenu.append(self.exportm)

        exit = Gtk.ImageMenuItem(Gtk.STOCK_QUIT, agr)
        key, mod = Gtk.accelerator_parse("<Control>q")
        exit.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
        exit.connect("activate", self.quit)
        filemenu.append(exit)
        mb.append(filem)

        # Edit menu
        editmenu = Gtk.Menu()
        edit = Gtk.MenuItem("Edit")
        edit.set_submenu(editmenu)

        self.recordm = Gtk.MenuItem("New Record")
        key, mod = Gtk.accelerator_parse("R")
        self.recordm.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
        self.recordm.connect("activate", self.newrecord)
        self.recordm.set_sensitive(False)
        editmenu.append(self.recordm)

        self.modifym = Gtk.MenuItem("Modify")
        key, mod = Gtk.accelerator_parse("E")
        self.modifym.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
        self.modifym.connect("activate", self.editmenumodify)
        self.modifym.set_sensitive(False)
        editmenu.append(self.modifym)

        self.deletem = Gtk.MenuItem("Delete")
        self.deletem.connect("activate", self.menuEditDel)
        self.deletem.set_sensitive(False)
        editmenu.append(self.deletem)

        sep = Gtk.SeparatorMenuItem()
        editmenu.append(sep)

        self.prefm = Gtk.MenuItem("Preferences")
        self.prefm.connect("activate", self.menuEditPreferences)
        self.prefm.set_sensitive(False)
        editmenu.append(self.prefm)

        mb.append(edit)

        # View menu
        viewmenu = Gtk.Menu()
        view = Gtk.MenuItem("View")
        view.set_submenu(viewmenu)

        self.summarym = Gtk.MenuItem("Show Summary")
        key, mod = Gtk.accelerator_parse("M")
        self.summarym.add_accelerator("activate", agr, key, mod, Gtk.AccelFlags.VISIBLE)
        self.summarym.connect("activate", self.menuViewSummary)
        self.summarym.set_sensitive(False)
        viewmenu.append(self.summarym)

        sep = Gtk.SeparatorMenuItem()
        viewmenu.append(sep)

        stat = Gtk.CheckMenuItem("Show Statusbar")
        stat.set_active(True)
        stat.connect("activate", self.on_status_view)
        viewmenu.append(stat)

        mb.append(view)

        # Plot menu
        plotmenu = Gtk.Menu()
        self.plot = Gtk.MenuItem("Plot")
        self.plot.set_sensitive(False)
        self.plot.set_submenu(plotmenu)
        self.plot.connect("activate", self.updateMenuPlot)

        self.plotmpdm = Gtk.MenuItem("Miles/Day")
        self.plotmpdm.connect("activate", self.menuPlot, 'mpd')
        plotmenu.append(self.plotmpdm)

        self.plotmpgm = Gtk.MenuItem("Miles/Gal")
        self.plotmpgm.connect("activate", self.menuPlot, 'mpg')
        plotmenu.append(self.plotmpgm)

        self.plotdpgm = Gtk.MenuItem("Dollars/Gal")
        self.plotdpgm.connect("activate", self.menuPlot, 'dpg')
        plotmenu.append(self.plotdpgm)

        self.plotdpmm = Gtk.MenuItem("Dollars/Mile")
        self.plotdpmm.connect("activate", self.menuPlot, 'dpm')
        plotmenu.append(self.plotdpmm)

        self.plotdpdm = Gtk.MenuItem("Dollars/Day")
        self.plotdpdm.connect("activate", self.menuPlot, 'dpd')
        plotmenu.append(self.plotdpdm)

        sep = Gtk.SeparatorMenuItem()
        plotmenu.append(sep)

        self.menuPlotTimeScale = Gtk.MenuItem("Time Scale")
        #self.plotdpdm.connect("activate", self.menuPlot, 'dpd')
        plotmenu.append(self.menuPlotTimeScale)

        self.menuPlotTimeScaleMenu = Gtk.Menu()

        self.menuPlotTimeScaleMenuAll = Gtk.MenuItem("All Time")
        self.menuPlotTimeScaleMenuAll.connect("activate", self.hookMenuPlotTimeScale, "all")
        self.menuPlotTimeScaleMenu.append(self.menuPlotTimeScaleMenuAll)

        self.menuPlotTimeScaleMenuYear = Gtk.MenuItem("Last Year")
        self.menuPlotTimeScaleMenuYear.connect("activate", self.hookMenuPlotTimeScale, "year")
        self.menuPlotTimeScaleMenu.append(self.menuPlotTimeScaleMenuYear)

        self.menuPlotTimeScaleMenuPeriodic = Gtk.MenuItem("Year Periodic")
        self.menuPlotTimeScaleMenuPeriodic.connect("activate", self.hookMenuPlotTimeScale, "periodic")
        self.menuPlotTimeScaleMenu.append(self.menuPlotTimeScaleMenuPeriodic)

        self.menuPlotTimeScale.set_submenu(self.menuPlotTimeScaleMenu)

        sep = Gtk.SeparatorMenuItem()
        plotmenu.append(sep)

        self.plotMenuClearAnnot = Gtk.MenuItem("Clear Highlight")
        self.plotMenuClearAnnot.connect("activate", self.clearAnnot)
        self.plotMenuClearAnnot.set_sensitive(False)
        plotmenu.append(self.plotMenuClearAnnot)

        self.plotMenuSave = Gtk.MenuItem("Save to File...")
        self.plotMenuSave.connect("activate", self.plotSave)
        self.plotMenuSave.set_sensitive(False)
        plotmenu.append(self.plotMenuSave)

        mb.append(self.plot)

        # Help menu
        helpmenu = Gtk.Menu()
        help = Gtk.MenuItem("Help")
        help.set_submenu(helpmenu)

        aboutm = Gtk.MenuItem("About")
        aboutm.connect("activate", self.openAboutWindow)
        helpmenu.append(aboutm)

        mb.append(help)

        ### Main window guts
        self.statusbar = Gtk.Statusbar()
        self.statusbar.push(1, "Ready")

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(mb, False, False, 0)

        # create the TreeView
        self.treeview = Gtk.TreeView()
        # TODO add ability to sort by headers
        self.treeview.set_headers_clickable(True)
        # rules-hint
        self.treeview.set_rules_hint(True);

        # create the TreeViewColumns to display the data
        self.tvcolumn = [None] * len(columnNames)
        for n in range(0, len(columnNames)):
            cell = Gtk.CellRendererText()
            if (fullFields[n] in numFields):
                cell.set_property('xalign', 1.0)
            self.tvcolumn[n] = Gtk.TreeViewColumn(columnNames[n], cell)
            self.tvcolumn[n].set_cell_data_func(cell, self.format_comment, fullFields[n])
            self.tvcolumn[n].set_resizable(True)
            self.treeview.append_column(self.tvcolumn[n])

        self.treeview.connect('row-activated', self.editrecord)
        self.treeview.connect('cursor-changed', self.on_row_select)
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.add(self.treeview)
        vbox.pack_start(self.scrolledwindow, True, True, 0)

        vbox.pack_start(self.statusbar, False, False, 0)
        self.window.add(vbox)

        self.window.connect("destroy", self.quit)
        self.window.connect('delete_event', self.quit)
        self.window.show_all()

        if (len(sys.argv) > 1):
            self.internOpenFile(sys.argv[1])

    def quit(self, widget, data=None):
        if self.database.dirty_bit:
            diag = Gtk.MessageDialog(self.window,
                Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING,
                Gtk.ButtonsType.OK_CANCEL,
                "There are unsaved changes. Close without saving?")
            diag.connect('response', self.quitResponse)
            diag.show()
        else:
            UserPrefs.save()
            Gtk.main_quit()

        return True

    def quitResponse(self, widget, response, data=None):
        if response == Gtk.ResponseType.OK:
            UserPrefs.save()
            Gtk.main_quit()
        else:
            widget.destroy()

    def newstatus(self, string):
        self.statusbar.pop(1)
        print(string)
        self.statusbar.push(1, string)

    def get_current_row(self):
        model, it = self.treeview.get_selection().get_selected()
        if it is None:
            return None
        return model.get_value(it, 0)

    def on_row_select(self, widget):
        row = self.get_current_row()
        self.modifym.set_sensitive(True)
        self.deletem.set_sensitive(True)
        if (self.isPlotActive()): # gnuplot pipe is open
            if (self.database.getText(row, self.plot_type) == invalidStr):
                self.newstatus("Cannot annotate plot, null data point.");
            else:
                # highlight the corresponding point in the plot
                #self.gnuplot_p.stdin.write("replot" + "\n")
                self.gnuplot_annot = ", \"< echo %d %s\" using 1:2 with points lt 3 pt 3" % (
                    time.mktime(self.database[row].date.timetuple()),
                    self.database.getText(row, self.plot_type))
                self.plotData(self.plot_type)

        return

    def clearAnnot(self, widget):
        self.gnuplot_annot = ""
        self.plotData(self.plot_type)
        return

    def on_file_loaded(self):
        self.saveasm.set_sensitive(True)
        self.exportm.set_sensitive(True)
        self.recordm.set_sensitive(True)
        self.modifym.set_sensitive(True)
        self.deletem.set_sensitive(True)
        self.summarym.set_sensitive(True)
        self.plot.set_sensitive(True)
        self.propm.set_sensitive(True)
        self.prefm.set_sensitive(True)
        return

    def menuFileNew(self, widget):
        self.database.newfile()
        VehProperties.clear()
        self.recordList = Gtk.ListStore(object)

        # Persuade the user to fill out the file properties
        self.menuFileProperties(widget)

        # Load new interface
        self.makeClean()
        self.on_file_loaded()
        self.treeview.set_model(self.recordList)
        self.newstatus("New file created")

        return

    def menuOpenFile(self, widget):
        dialog = Gtk.FileChooserDialog("Choose file", None, Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                       Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_transient_for(self.window)

        filter = Gtk.FileFilter()
        filter.set_name("XML files")
    # since you create a dialect of XML, you can change the file extension, but I don't know what to call it yet
        filter.add_pattern("*.xml")
        filter.add_pattern("*.pmx") # PyMPG XML?
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("CSV files")
        filter.add_pattern("*.csv")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.internOpenFile(dialog.get_filename())

        elif response == Gtk.ResponseType.CANCEL:
            self.newstatus('No file selected')
        dialog.destroy()

        return

    def internOpenFile(self, filename):
        self.database.loadFile(filename)
        # Load new interface
        self.makeClean()
        self.on_file_loaded()

        self.updateList()

        self.newstatus("'" + self.database.filename + "' loaded")

        return

    def menuFileSave(self, widget):
        # check that a filename is set
        if (self.database.filename == ""):
            self.menuFileSaveAs(widget)

        # write the file that is open
        self.internFileSave()
        return

    def menuFileSaveAs(self, widget):
        dialog = Gtk.FileChooserDialog(title="Choose file name...",
                                       action=Gtk.FileChooserAction.SAVE,
                                       buttons=(Gtk.STOCK_CANCEL,
                                                Gtk.ResponseType.CANCEL,
                                                Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
                                       )

        dialog.set_default_response(Gtk.ResponseType.OK)

    # TODO this is the same as file open... combine
        filter = Gtk.FileFilter()
        filter.set_name("XML files")
        filter.add_pattern("*.xml")
        filter.add_pattern("*.pmx")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("CSV files")
        filter.add_pattern("*.csv")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # maybe do some checking of the file name here
            #self.newstatus("New file name is %s" % dialog.get_filename())
            self.database.filename = dialog.get_filename()
            self.internFileSave()

        elif response == Gtk.ResponseType.CANCEL:
            self.newstatus('No file selected')
            return

        dialog.destroy()

        return

    def internFileSave(self):
    # TODO this might change
        self.database.saveFile()

        self.makeClean()
        self.newstatus("File '%s' saved." % self.database.filename)

        return


    def menuFileExport(self, widget):
        dialog = Gtk.FileChooserDialog(title="Save waveform as...",
                                       action=Gtk.FileChooserAction.SAVE,
                                       buttons=(Gtk.STOCK_CANCEL,
                                                Gtk.ResponseType.CANCEL,
                                                Gtk.STOCK_SAVE,
                                                Gtk.ResponseType.OK))
        dialog.set_current_name(self.database.filename.replace('.csv', '.wfm'))

        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name("WFM files")
        filter.add_pattern("*.wfm")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            self.newstatus('No file selected')
            dialog.destroy()
            return

        filename = dialog.get_filename()
        dialog.destroy()

        # save the file that is open
        self.database.exportWaveform(filename)

        self.newstatus('Exported waveform to %s' % filename)

        return

    def menuFileProperties(self, widget):
        editwindow = Gtk.Window()
        editwindow.set_title("Vehicle Preferences")
        #editwindow.set_size_request(400,300)

        table = Gtk.Table(len(vehPrefFields) + 1, 2, False)

        for x in range(0, len(vehPrefFields)):
            field = vehPrefFields[x]
            label = Gtk.Label(field)
            table.attach(label, 0, 1, x, x + 1)

            entry = Gtk.Entry()
            if (field in VehProperties):
                entry.set_text(VehProperties[field])

            entry.connect("activate", self.updateProperty, field)
            entry.connect("focus-out-event", self.propWindowEntryFocusOut, field)
            table.attach(entry, 1, 2, x, x + 1)

        editwindow.add(table)

        editwindow.show_all()
        self.newstatus("Opened window to edit vehicle properties")

        return


    def updateProperty(self, entry, field):
        if (field not in VehProperties or entry.get_text() != VehProperties[field]):
            self.makeDirty()

            VehProperties[field] = entry.get_text()

            # redraw main window here
            self.newstatus("Updated %s property" % field)

        return

    def propWindowEntryFocusOut(self, widget, event, field):
        # this basically throws out the 'event'
        return self.updateProperty(widget, field)

    def menuEditPreferences(self, widget):
        editwindow = Gtk.Window()
        editwindow.set_title("User Preferences")

        table = Gtk.Table(len(UserPrefs) + 1, 2, False)

        for section in ['gnuplot']:
            for x, key in enumerate(UserPrefs[section]):
                field = UserPrefs.keys()[x]
                label = Gtk.Label(field)
                table.attach(label, 0, 1, x, x + 1)

                entry = Gtk.Entry()
                entry.set_text(UserPrefs[section][field])

                entry.connect("activate", self.updatePreference, field)
                entry.connect("focus-out-event", self.prefWindowEntryFocusOut, field)
                table.attach(entry, 1, 2, x, x + 1)

        editwindow.add(table)

        editwindow.show_all()
        self.newstatus("Opened window to edit preferences")

        return


    def updatePreference(self, entry, field):
        if (entry.get_text() != UserPrefs[field]):
            self.makeDirty()

            UserPrefs[field] = entry.get_text()

            # redraw main window here
            self.newstatus("Updated %s preference" % field)

        return

    def prefWindowEntryFocusOut(self, widget, event, field):
        # this basically throws out the 'event'
        return self.updatePreference(widget, field)

    def menuEditDel(self, widget):
        # TODO ask user if they're sure when I learn how

        row = self.get_current_row()
        self.deleteRecord(row)
        return

    def menuViewSummary(self, widget):
        self.createSummaryWindow()
        return

    def editmenumodify(self, widget):
        row = self.get_current_row()
        self.createEditWindow(modelrow)
        return

    # this is much more straightforward than some other things I was doing for set_sensitive.
    # Need to implement this mechanism there.
    def updateMenuPlot(self, widget):
        self.plotMenuClearAnnot.set_sensitive(self.gnuplot_annot != "")
        self.plotMenuSave.set_sensitive(self.isPlotActive())
        return

    def changeTimeScale(self, field):
        self.timeScale = field
        self.updatePlot()
        return

    def hookMenuPlotTimeScale(self, widget, field):
        self.changeTimeScale(field)
        return

    def menuPlot(self, widget, field):
        self.plotData(field)
        return

    def isPlotActive(self):
        return (self.gnuplot_p != False and self.gnuplot_p.poll() is None)

    def updatePlot(self):
        if (self.isPlotActive()):
            self.plotData(self.plot_type)
        return

    def plotData(self, field):
        if (self.plot_type != field):
            self.gnuplot_annot = ""

        self.plot_type = field # Save the type of plot that was requested

        titles = {'mpd': 'Mileage per Day',
            'mpg': 'Fuel Economy',
            'dpg': 'Fuel Price per Gallon',
            'dpm': 'Fuel Cost per Mile',
            'dpd': 'Fuel Cost per Day',
            }
        ylabels = {'mpd': 'Miles per Day [mi/day]',
            'mpg': 'Miles per Gallon [mi/gal]',
            'dpg': 'Dollars per Gallon [$/gal]',
            'dpm': 'Dollars per Mile [$/mi]',
            'dpd': 'Dollars per Day [$/day]',
            }

        commands = [
        # having trouble with default 'aqua' on Mac OSX
        # use 'wxt' or 'windows' for Windows
            ("set term %s" % UserPrefs['GnuPlotTerm'] if ('GnuPlotTerm' in UserPrefs) and (UserPrefs['GnuPlotTerm'].strip() != "") else ""),
            "set xdata time" if (self.timeScale != "periodic") else "set xdata",
            "set timefmt '%s'" if (self.timeScale != "periodic") else "",
            #"set xtics rotate by 90",
            "set xtics nomirror rotate by -45" if (self.timeScale != "periodic") else "set xtics rotate by 0",
            "set autoscale",
            "set log y" if (field == "mpd" or field == "dpd") else "unset log",
            "set key" if (self.timeScale == "periodic") else "unset key",
            "set grid",

            "set title '%s'" % titles[field],
            "set xlabel 'Date'" if (self.timeScale != "periodic") else "set xlabel 'Day of the Year'",
            "set ylabel '%s'" % ylabels[field],
            ]

        if (not self.isPlotActive()):
            print(UserPrefs['GnuPlotPath'])
            self.gnuplot_p = subprocess.Popen(
                UserPrefs['GnuPlotPath'], shell=True,
                stdin=subprocess.PIPE,
                #stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
                )
            #gnuplot_in = open('gnuplot.in', 'w')
            #print self.gnuplot_p.stdout.readline()

        for cmd in commands:
            if (self.gnuplot_p.poll() != None):
                print("GNUPLOT terminated.")
                return

            #print >> gnuplot_in, cmd
            self.gnuplot_p.stdin.write(cmd + "\n")


        oldestDate = mktimestamp(self.database[-1].date) - 31557600.0 #6*(52.0/12)*7*24*3600
        print("Data range: " + str(self.database[1].date) + " to " + str(self.database[-1].date))
        print("Plot range: " + fmttimestamp(oldestDate) + " to " + str(self.database[-1].date))
        # TODO make function for time.mktime(time).timetuple()

        # write each of the records to the pipe
        if (self.timeScale == "periodic"):
            cmdStr = []
            for year in range(self.database[1].date.year, self.database[-1].date.year+1):
                cmdStr.append(" '-' using 1:2 with lines title '%s'" % year)

            self.gnuplot_p.stdin.write("plot " + ", ".join(cmdStr) + "\n")

            for year in range(self.database[1].date.year, self.database[-1].date.year+1):
                for x in range(0, len(self.database.recordTable)):
                    if ( (self.database[x].date.year == year) and self.database.getText(x, field) != invalidStr ):
                        # Here, I want the day of the year
                        secs = "%d" % (self.database[x].date.timetuple().tm_yday)
                        wfmstr = secs + "\t" + self.database.getText(x, field) + "\n"
                        self.gnuplot_p.stdin.write(wfmstr)
            self.gnuplot_p.stdin.write("e\n")

        else:
            # the %s here allows me to annotate a point with a string
            self.gnuplot_p.stdin.write("plot '-' using 1:2 with lines%s\n" % self.gnuplot_annot)
            for x in range(0, len(self.database.recordTable)):
                if ( (self.timeScale == "all" or \
                    (self.timeScale == "year" and (mktimestamp(self.database[x].date) > oldestDate) ) \
                    and not (field == "mpg" and not self.database[x].fill))):
                    # Convert the datetime obj to Epoch seconds
                    secs = "%d" % time.mktime(self.database[x].date.timetuple())
                    wfmstr = secs + "\t" + self.database.getText(x, field) + "\n"
                    #print >> gnuplot_in, wfmstr
                    self.gnuplot_p.stdin.write(wfmstr)
                self.gnuplot_p.stdin.write("e\n")

        #self.gnuplot_p.stdout.read()

        self.newstatus("Generated %s plot." % titles[field])
        #gnuplot_in.flush(); gnuplot_in.close()

        return

    def plotSave(self, widget):
        dialog = Gtk.FileChooserDialog(title="Save plot as...", action=Gtk.FileChooserAction.SAVE, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_current_name(self.database.filename.replace('.csv', '.ps'))

        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name("PostScript files")
        filter.add_pattern("*.ps")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            self.newstatus('No file selected')
            dialog.destroy()
            return

        plotFileName = dialog.get_filename()
        dialog.destroy()

        # TODO use ''' here
        self.gnuplot_p.stdin.write(
            "set term push\n"
            + "set term postscript enhanced color\n"
            + "set output \"%s\"\n" % plotFileName
            + "set noborder\n");
        self.plotData(self.plot_type)
        self.gnuplot_p.stdin.write(
            "set term pop\n"
            + "replot\n");

        self.newstatus("Saved plot to '%s'." % plotFileName);
        return

    def newrecord(self, widget):
        editwindow = EditWindow(self, self.database, None)
        editwindow.open()
        return

    def updateList(self):
        self.recordList = Gtk.ListStore(object)
# TODO improve sorting flexibility here
        for i in range(len(self.database.recordTable) - 1, -1, -1):
        #for i in range(0, len(self.database.recordTable)):
            self.recordList.append([i])
        self.treeview.set_model(self.recordList)

        return

    def deleteRecord(self, row):
        del self.database[row]

        self.updateList()

        self.makeDirty()
        self.newstatus("Deleted record %d" % (row + 1))
        return

    def editrecord(self, tree, path, column):
        self.createEditWindow(self.get_current_row())
        return

    def openAboutWindow(self, widget):
        about = Gtk.AboutDialog()
        about.set_program_name(progname)
        about.set_version(progver)
        about.set_copyright(progcopy)
        about.set_comments(progcomm)
        about.set_website(progurl)
        about.set_logo(pumppb)
        about.run()
        about.destroy()
        return

    def createSummaryWindow(self):
        summaryWindow = Gtk.Window()
        summaryWindow.set_title("Summary")

        tableLabels = self.database.getSummaryTable()

        numRows = len(tableLabels)/3

        table = Gtk.Table(numRows, 2, False)
        for i in range(0, numRows):
            myLabel = Gtk.Label(tableLabels[3 * i])
            myLabel.set_alignment(0, 0.5)
            table.attach(myLabel, 1, 2, i, i + 1, ypadding=4, xpadding=8)

            myLabel = Gtk.Label(tableLabels[3 * i + 1])
            myLabel.set_alignment(1, 0.5)
            table.attach(myLabel, 2, 3, i, i + 1, ypadding=4, xpadding=8)

            myLabel = Gtk.Label(tableLabels[3 * i + 2])
            myLabel.set_alignment(0, 0.5)
            table.attach(myLabel, 3, 4, i, i + 1, ypadding=4, xpadding=8)

            # Dump to terminal too (makes easy copy & paste)
            print(tableLabels[3 * i], "\t", tableLabels[3 * i + 1], "\t", tableLabels[3 * i + 2])

        summaryWindow.add(table)
        summaryWindow.show_all()
        self.newstatus("Summary generated.")

        return

    def createEditWindow(self, row):
        editwindow = EditWindow(self, self.database, row)
        editwindow.open()
        self.newstatus("Opened window to edit record %d" % (row + 1))
        return

    def updateBool(self, button, window, col):
        if (window.row==None) or (button.get_active() != (self.database[window.row][storedFields[col]] == "Yes")):
            self.makeDirty()
            self.database[window.row][storedFields[col]] = button.get_active()
            self.newstatus("Set %s to %s on record %d" %
                           (storedFieldLabels[col],
                            "Yes" if button.get_active() else "No", window.row)
                           )
            self.updateList()
            self.window.queue_draw()

    def updateField(self, entry, editwindow, col):
        # Check for change
        if type(entry) == type(Gtk.CheckButton()):
            if entry.get_active() != self.database.getText(editwindow.row, storedFields[col]) :
                self.makeDirty()
                self.database[editwindow.row].setText(storedFields[col], "Yes" if entry.get_active() else "No")

        else:
            if entry.get_text() != self.database.getText(editwindow.row, storedFields[col]) :
                self.makeDirty()

            # need to catch exceptions here and throw up errors
            try:
                self.database[editwindow.row].setText(storedFields[col], entry.get_text())

                if (col == sortField):
                    key = self.database[editwindow.row][storedFields[sortField]]
                    self.database.sortRecords()
                    newrow = self.database.getRowOf(key)
                    if (newrow != editwindow.row):
                        editwindow.row = newrow
                        self.updateList()
                        editwindow.update() # to update the edit window title
                        self.newstatus("Warning: You have changed the position of the record to %d" % (newrow+1))

            except ValueError:
                print('Caught ValueError')
                self.show_error('Invalid format, try again.')
                return

        self.selectRow(editwindow.row)

        # redraw main window here
        self.newstatus("Updated %s on record %d" % (storedFieldLabels[col], (editwindow.row+1)))
        self.window.queue_draw()
        self.updatePlot()

        return

    def selectRow(self, row):
        self.treeview.set_cursor(len(self.database) - row - 1)

    def show_error (self, string):
        md = Gtk.MessageDialog(None,
            Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.CLOSE, string)
        md.run()
        md.destroy()

    def format_comment(self, column, cell, model, it, field):
        row = model.get_value(it, 0)
        #row = self.get_current_row()
        cell.set_property('text', self.database.getText(row, field))
        return

    def makeDirty(self):
        if (not self.database.dirty_bit):
            self.newstatus("File modified")
            self.database.dirty_bit = True
            self.savem.set_sensitive(True)
            self.setWindowTitle()

        return

    def makeClean(self):
        self.database.dirty_bit = False
        self.setWindowTitle()
        self.savem.set_sensitive(False)
        return

    def setWindowTitle(self):
        if (self.database.filename == ""):
            self.window.set_title(progname)
        else:
            file_basename = self.database.filename.split('/')[-1]
            file_basename = file_basename.split('\\')[-1] # for Winblows compat
            self.window.set_title("%s - %s%s" % (progname,
                (" ".join(VehProperties[field] for field in ['Year', 'Make', 'Model']) + ' (' + file_basename + ')') if VehProperties['Make'] != "" else file_basename,
                "*" if self.database.dirty_bit else ""))
        return

    def on_status_view(self, widget):
        if widget.active:
            self.statusbar.show()
        else:
            self.statusbar.hide()


if __name__ == '__main__':
    UserPrefs = UserPrefManager()

    gui = PyMPG()
    #gui.window.destroy()
    Gtk.main()
