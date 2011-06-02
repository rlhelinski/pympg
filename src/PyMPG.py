#!/usr/bin/python
#
#    PyMPG - Python Mileage Processing GUI
#
# Ryan Helinski


import sys
import gtk
import glib
import csv
import time
import datetime
#import traceback
import subprocess

# Global settings 
progname = "PyMPG"
progver = "1.1b"
progcopy = "Copyright Ryan Helinski"
progcomm = "A simple tool for keeping track of gas mileage implemented in Python using PyGTK."
progurl = "http://pgmdb.sf.net/"

invalidStr = "--"
dateFmtStr = "%Y/%m/%d"

daysPerYear = 365.25
numSigFigs = 3

pumpxpm = sys.path[0] + "/pump.png"
try: 
    pumppb = gtk.gdk.pixbuf_new_from_file(pumpxpm) 
except glib.GError as error:
	print error

# http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python/1695250#1695250
class Enum():
    def __init__(self, *sequential, **named):
        self.enumd = dict(zip(sequential, range(len(sequential))), **named)
    def __len__(self):
        return len(self.enumd)
    def __getitem__(self, index):
        try:
            return self.enumd.keys()[self.enumd.values().index(index)]
        except ValueError:
            raise IndexError
    def __getattr__(self, name):
        if name in self.enumd:
            return self.enumd[name]
        raise AttributeError
    def value(self, name):
        return self.enumd[name]
    def pairs(self):
	return self.enumd.items()

# http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python/4590052#4590052
def xml_indent(elem, level=0):
    """Add white space to XML DOM so that when it is converted to a string, it is pretty."""

    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            xml_indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def mktimestamp(timeobj):
	return int(time.mktime(timeobj.timetuple()))

def fmttimestamp(timestamp):
	return datetime.datetime.fromtimestamp(timestamp).strftime(dateFmtStr)

# TODO most of these should move to the record class
storedFields = Enum('odo', 'date', 'gals', 'dpg', 'location', 'station', 'fill', 'comment')
storedFieldLabels = Enum('Odometer', 'Date', 'Gallons', 'Price / Gal', 'Location', 'Station', 'Filled?', 'Comment')

fullFields = Enum('odo', 'date', 'days', 'dist', 'gals', 'mpg', 'dpg', 'tankcost', 'mpd', 'dpd', 'station', 'location', 'fill', 'comment')
columnNames = Enum('Odo.', 'Date', 'Days', 'Dist.', 'Gals', 'mi/gal', '$/gal', 'Cost', 'mi/day', '$/day', 'Station', 'Location', 'Fill?', 'Comment')

numFields = Enum('odo', 'date', 'days', 'dist', 'gals', 'mpg', 'dpg', 'tankcost', 'mpd', 'dpd')

# columns to put into waveform
wfmcols = Enum('date', 'days', 'odo', 'dist', 'gals', 'dpg', 'tankcost', 'mpd', 'mpg')

sortField = storedFields.odo


# defaults
# TODO these should be part of the database, but they are not
UserPreferences = dict({'GnuPlotPath' : 'gnuplot', 'GnuPlotTerm' : 'x11'}) 
VehProperties = dict()
vehPrefFields = Enum("Year","Make","Model","TankSize","ServiceOffset","ServiceInterval","Owner")



class FuelRecord():

	def __init__(self, source=None):
		self.fields = dict()

		if (type(source) == None):
			None
		elif (type(source) == list):
			self.fromlist(source)
		elif (type(source) == dict):
			self.fromdict(source)

	def __getattr__(self, name): # object.name, return raw data
		return self.fields[name]

	def __repr__(self): # string representation
		return str(self.fields)

	def __getitem__(self, key): # object[name], format a string 
		return self.getText(key)

	def fromlist(self, row):
		if (len(row) != len(storedFields)):
			raise NameError('Wrong number of fields in CSV file!')
					
		for field, index in storedFields.pairs():
			self.fields[field] = self.formatText(field, row[index])

	def fromdict(self, mydict):
		for field in storedFields:
			self.fields[field] = self.formatText(field, mydict[field])

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
		if (field == "odo"):
			retval = int(text)
		elif (field == "date"):
			retval = datetime.datetime.strptime(text, dateFmtStr)
		elif (field == "gals" or field == "dpg"):
			retval = round(float(text), numSigFigs)
		elif (field == "fill"):
			retval = (text.lower() == "yes")
		else:	# return value as-is
			retval = text

		return retval

# This class opens/saves files, and manages the data in memory
class DataBase :
	dirty_bit = False		# true if the data from the file has been modified
	filename = ""		 # name of the file that's open
	recordTable = []		# the actual records
	
	def __getitem__(self, index):
		"""
		This prevents you from having to use the recordTable directly. 
		i.e., myDB.recordTable[index] -> myDB[index]
		"""
		return self.recordTable[index]

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
					UserPreferences[row[1]] = row[2]
					
				elif (row[0] == 'veh'):
					VehProperties[row[1]] = row[2] 
					
				else:
					self.recordTable.append(FuelRecord(row))
					
		elif (filename.lower().endswith('xml')):
			import xml.etree.ElementTree as etree
			mytree = etree.parse(filename)
			myroot = mytree.getroot()
			
			for child in myroot[0]:
				if (child.tag == 'user'):
					for pref in child:
						UserPreferences[pref.attrib['name']] = pref.attrib['value']
				if (child.tag == 'vehicle'):
					for pref in child:
						VehProperties[pref.attrib['name']] = pref.attrib['value']
				if (child.tag == 'fuel'):
					for record in child:
						 self.recordTable.append(FuelRecord(record.attrib))

		else: 
			raise NameError("Unknown file type")


		self.filename = filename # Save file name for later

		self.sortRecords()
		

		return

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
				lastFill = 1 
				totalFuel = self[row].gals
				while (not self[row - lastFill].fill):
					lastFill = lastFill + 1
					totalFuel = totalFuel + self[row - lastFill].gals

				totalMiles = self[row].odo - self[row - lastFill].odo
				return "%0.1f" % (totalMiles / totalFuel)
			
		elif (field == "dpd"):
			if (row == 0):
				return invalidStr

			try:
				# recursive calls here
				tankcost = float( self.getText(row, "tankcost") )
				days = float( self.getText(row, "days") )
				
				# dollars / day = tankcost / days 
				return "%0.2f" % (tankcost / days) 

				# dollars / day = ( dollars / gallon ) * ( miles / gallon ) ^ -1 * ( miles / day )
				#return "%0.2e" % (dpg / mpg * mpd)

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
	
	def saveFile(self):
		if (self.filename.lower().endswith('csv')):
			# Save records back to a CSV file
			fileWriter = csv.writer(open(self.filename, 'w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

			for pref in UserPreferences.keys():
				fileWriter.writerow(['pref', pref, UserPreferences[pref]])
			
			for prop in VehProperties.keys():
				fileWriter.writerow(['veh', prop, VehProperties[prop]])

			i = 0
			for i in range(0, len(self.recordTable)):
				fileWriter.writerow(self[i].tolist())

		elif (self.filename.lower().endswith('xml')):
			# Create an XML
			import xml.etree.ElementTree as etree

			myxml = etree.Element('xml', attrib={'version': '1.0', 'encoding': 'UTF-8'})
			mypmx = etree.SubElement(myxml, 'pmx', attrib={'version': '0.1', 'generator': sys.argv[0]})

			myuser = etree.SubElement(mypmx, 'user')
			for pref in UserPreferences.keys():
				etree.SubElement(myuser, 'pref', attrib={'name' : pref, 'value' : UserPreferences[pref]})

			myveh = etree.SubElement(mypmx, 'vehicle')
			for prop in VehProperties.keys():
				etree.SubElement(myveh, 'prop', attrib={'name' : prop, 'value' : VehProperties[prop]})

			myfuel = etree.SubElement(mypmx, 'fuel')

			i = 0
			for i in range(0, len(self.recordTable)):
				etree.SubElement(myfuel, 'record', attrib=self[i].todict())

			xmlfile = open(self.filename, 'w')
			xml_indent(myxml) # add white space to XML DOM to result in pretty printed string
			xmlfile.write(etree.tostring(myxml))
			xmlfile.flush()
			xmlfile.close()

		else:
			raise NameError('Unknown file type')

		return

	def addNewRecord(self, record=FuelRecord):

		#record.append(len(self.recordTable))
		self.recordTable.append(record) 
		self.sortRecords()
		
		return

	def sortRecords(self):
		self.recordTable.sort(recordCompare)
		return

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
					line += "%d" % time.mktime(self[x][storedFields.date].timetuple())
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
        
    def open(self):
        self.editwindow = gtk.Window()

        self.table = gtk.Table(len(storedFields) + 1, 2, False)
        for x in range(0, len(storedFields)):
            label = gtk.Label(storedFieldLabels[x])
            self.table.attach(label, 0, 1, x, x + 1)

            if (storedFields[x] == 'fill'):
                button = gtk.CheckButton(storedFieldLabels[x])
                button.set_active(self.database[self.row].fill)
                button.connect("clicked", self.interface.updateBool, self, x)
                self.table.attach(button, 1, 2, x, x + 1)
            else:
                entry = gtk.Entry()
                entry.set_text(self.database.getText(self.row, storedFields[x]))
                entry.connect("activate", self.interface.updateField, self, x)
                entry.connect("focus-out-event", self.editWindowEntryFocusOut, self, x)
                self.table.attach(entry, 1, 2, x, x + 1)

        self.editwindow.add(self.table)
        
        self.setWindowTitle()
        
        self.editwindow.show_all()

    def setWindowTitle(self):
        self.editwindow.set_title("Edit Record %d" % (self.row + 1))
        return

    def update(self):
        
        # all we have to do is update the row and the window title if the record moved
        #self.row = self.database.getRowOf(self.key)
        self.setWindowTitle()

        return

    def editWindowEntryFocusOut(self, widget, event, editwindow, col):
        # this basically throws out the 'event'
        return self.interface.updateField(widget, editwindow, col)



def recordCompare(a, b):
    return cmp(a.odo, b.odo)

# This class serves as an interface between other classes and the GTK user interface
class PyMPG:
    database = DataBase()   # a file interface class
    gnuplot_p = False        # not false if a pipe to GNUPLOT is open
    plot_type = ""        # type of plot that has been generated: 'mpd', 'mpg', or 'dpg'
    gnuplot_annot = ""        # extra string to add to GNUPLOT 'plot' command for annotating a graph
    timeScale = "all"

    def __init__(self, dname=None):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(progname)
        self.window.set_size_request(800, 600)
        self.window.set_position(gtk.WIN_POS_CENTER)
        try:
            self.window.set_icon(pumppb)
        except NameError as error:
            print error

        # Menu bar
        mb = gtk.MenuBar()
        # File menu
        filemenu = gtk.Menu()
        filem = gtk.MenuItem("_File")
        filem.set_submenu(filemenu)
       
        agr = gtk.AccelGroup()
        self.window.add_accel_group(agr)

        newi = gtk.ImageMenuItem(gtk.STOCK_NEW, agr)
        key, mod = gtk.accelerator_parse("N")
        newi.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        newi.connect("activate", self.menuFileNew)
        filemenu.append(newi)

        openm = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        key, mod = gtk.accelerator_parse("O")
        openm.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        openm.connect("activate", self.menuOpenFile)
        filemenu.append(openm)

        self.savem = gtk.ImageMenuItem(gtk.STOCK_SAVE, agr)
        key, mod = gtk.accelerator_parse("S")
        self.savem.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.savem.set_sensitive(False)
        self.savem.connect("activate", self.menuFileSave)
        filemenu.append(self.savem)

        self.saveasm = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS, agr)
        self.saveasm.set_sensitive(False)
        self.saveasm.connect("activate", self.menuFileSaveAs)
        filemenu.append(self.saveasm)

        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)
        
        self.propm = gtk.MenuItem("Properties")
        self.propm.set_sensitive(False)
        self.propm.connect("activate", self.menuFileProperties)
        filemenu.append(self.propm)

        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)

        self.exportm = gtk.MenuItem("Export Waveform")
        self.exportm.set_sensitive(False)
        self.exportm.connect("activate", self.menuFileExport)
        filemenu.append(self.exportm)

        exit = gtk.ImageMenuItem(gtk.STOCK_QUIT, agr)
        key, mod = gtk.accelerator_parse("Q")
        exit.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        exit.connect("activate", self.quit)
        filemenu.append(exit)
        mb.append(filem)

        # Edit menu
        editmenu = gtk.Menu()
        edit = gtk.MenuItem("Edit")
        edit.set_submenu(editmenu)

        self.recordm = gtk.MenuItem("New Record")
        key, mod = gtk.accelerator_parse("R")
        self.recordm.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.recordm.connect("activate", self.newrecord)
        self.recordm.set_sensitive(False)
        editmenu.append(self.recordm)

        self.modifym = gtk.MenuItem("Modify")
        key, mod = gtk.accelerator_parse("E")
        self.modifym.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.modifym.connect("activate", self.editmenumodify)
        self.modifym.set_sensitive(False)
        editmenu.append(self.modifym)

        self.deletem = gtk.MenuItem("Delete")
        self.deletem.connect("activate", self.menuEditDel)
        self.deletem.set_sensitive(False)
        editmenu.append(self.deletem)

        sep = gtk.SeparatorMenuItem()
        editmenu.append(sep)
        
        self.prefm = gtk.MenuItem("Preferences")
        self.prefm.connect("activate", self.menuEditPreferences)
        self.prefm.set_sensitive(False)
        editmenu.append(self.prefm)

        mb.append(edit)

        # View menu
        viewmenu = gtk.Menu()
        view = gtk.MenuItem("View")
        view.set_submenu(viewmenu)

        self.summarym = gtk.MenuItem("Show Summary")
        key, mod = gtk.accelerator_parse("M")
        self.summarym.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.summarym.connect("activate", self.menuViewSummary)
        self.summarym.set_sensitive(False)
        viewmenu.append(self.summarym)

        sep = gtk.SeparatorMenuItem()
        viewmenu.append(sep)

        stat = gtk.CheckMenuItem("Show Statusbar")
        stat.set_active(True)
        stat.connect("activate", self.on_status_view)
        viewmenu.append(stat)
        
        mb.append(view)

        # Plot menu
        plotmenu = gtk.Menu()
        self.plot = gtk.MenuItem("Plot")
        self.plot.set_sensitive(False)
        self.plot.set_submenu(plotmenu)
        self.plot.connect("activate", self.updateMenuPlot)

        self.plotmpdm = gtk.MenuItem("Miles/Day")
        self.plotmpdm.connect("activate", self.menuPlot, 'mpd')
        plotmenu.append(self.plotmpdm)

        self.plotmpgm = gtk.MenuItem("Miles/Gal")
        self.plotmpgm.connect("activate", self.menuPlot, 'mpg')
        plotmenu.append(self.plotmpgm)

        self.plotdpgm = gtk.MenuItem("Dollars/Gal")
        self.plotdpgm.connect("activate", self.menuPlot, 'dpg')
        plotmenu.append(self.plotdpgm)
        
        self.plotdpdm = gtk.MenuItem("Dollars/Day")
        self.plotdpdm.connect("activate", self.menuPlot, 'dpd')
        plotmenu.append(self.plotdpdm)
        
        sep = gtk.SeparatorMenuItem()
        plotmenu.append(sep)

        self.menuPlotTimeScale = gtk.MenuItem("Time Scale")
        #self.plotdpdm.connect("activate", self.menuPlot, 'dpd')
        plotmenu.append(self.menuPlotTimeScale)

	self.menuPlotTimeScaleMenu = gtk.Menu()

	self.menuPlotTimeScaleMenuAll = gtk.MenuItem("All Time")
	self.menuPlotTimeScaleMenuAll.connect("activate", self.hookMenuPlotTimeScale, "all")
	self.menuPlotTimeScaleMenu.append(self.menuPlotTimeScaleMenuAll)

	self.menuPlotTimeScaleMenuMonth = gtk.MenuItem("Last Year")
	self.menuPlotTimeScaleMenuMonth.connect("activate", self.hookMenuPlotTimeScale, "year")
	self.menuPlotTimeScaleMenu.append(self.menuPlotTimeScaleMenuMonth)

	self.menuPlotTimeScale.set_submenu(self.menuPlotTimeScaleMenu)
        
        sep = gtk.SeparatorMenuItem()
        plotmenu.append(sep)

        self.plotMenuClearAnnot = gtk.MenuItem("Clear Highlight")
        self.plotMenuClearAnnot.connect("activate", self.clearAnnot)
        self.plotMenuClearAnnot.set_sensitive(False)
        plotmenu.append(self.plotMenuClearAnnot)

        self.plotMenuSave = gtk.MenuItem("Save to File...")
        self.plotMenuSave.connect("activate", self.plotSave)
        self.plotMenuSave.set_sensitive(False)
        plotmenu.append(self.plotMenuSave)

        mb.append(self.plot)

        # Help menu
        helpmenu = gtk.Menu()
        help = gtk.MenuItem("Help")
        help.set_submenu(helpmenu)

        aboutm = gtk.MenuItem("About")
        aboutm.connect("activate", self.openAboutWindow)
        helpmenu.append(aboutm)

        mb.append(help)

        ### Main window guts
        self.statusbar = gtk.Statusbar()
        self.statusbar.push(1, "Ready")

        vbox = gtk.VBox(False, 2)
        vbox.pack_start(mb, False, False, 0)

        # create the TreeView
        self.treeview = gtk.TreeView()
        self.treeview.set_headers_clickable(True)
        # rules-hint
        self.treeview.set_rules_hint(True);

        # create the TreeViewColumns to display the data
        self.tvcolumn = [None] * len(columnNames)
        for n in range(0, len(columnNames)):
            cell = gtk.CellRendererText()
            if (fullFields[n] in numFields):
                #print "Yes"
                #self.tvcolumn[n].set_alignment(1.0)
                #import pango
                #cell.set_property('alignment', pango.ALIGN_RIGHT)
                cell.set_property('xalign', 1.0)
            self.tvcolumn[n] = gtk.TreeViewColumn(columnNames[n], cell)
            self.tvcolumn[n].set_cell_data_func(cell, self.format_comment, fullFields[n])
            self.treeview.append_column(self.tvcolumn[n])

        self.treeview.connect('row-activated', self.editrecord)
        self.treeview.connect('cursor-changed', self.on_row_select)
        self.scrolledwindow = gtk.ScrolledWindow()
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
            diag = gtk.MessageDialog(self.window,
                gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                gtk.BUTTONS_OK_CANCEL,
                "There are unsaved changes. Close without saving?")
            diag.connect('response', self.quitResponse)
            diag.show()
        else:
            gtk.main_quit()

        return True

    def quitResponse(self, widget, response, data=None):
        if response == gtk.RESPONSE_OK:
            gtk.main_quit()
        else:
            widget.destroy()

    def newstatus(self, string):
        self.statusbar.pop(1)
        print string
        self.statusbar.push(1, string)

    def get_current_row(self):
        model, it = self.treeview.get_selection().get_selected()
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
        self.recordList = gtk.ListStore(object)
        
        # Persuade the user to fill out the file properties
        self.menuFileProperties(widget)
        
        # Load new interface
        self.makeClean()
        self.on_file_loaded()
        self.treeview.set_model(self.recordList)
        self.newstatus("New file created")

        return
    
    def menuOpenFile(self, widget):
        dialog = gtk.FileChooserDialog("Choose file", None, gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                       gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name("XML files")
	# since you create a dialect of XML, you can change the file extension, but I don't know what to call it yet 
        filter.add_pattern("*.xml") 
        filter.add_pattern("*.pmx") # Python MPG XML? 
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("CSV files")
        filter.add_pattern("*.csv")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.internOpenFile(dialog.get_filename())

        elif response == gtk.RESPONSE_CANCEL:
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
        dialog = gtk.FileChooserDialog(title="Choose file name...",
                                       action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                       buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_SAVE, gtk.RESPONSE_OK)
                                       )
        
        dialog.set_default_response(gtk.RESPONSE_OK)

	# TODO this is the same as file open... combine
        filter = gtk.FileFilter()
        filter.set_name("XML files")
        filter.add_pattern("*.xml")
        filter.add_pattern("*.pmx")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("CSV files")
        filter.add_pattern("*.csv")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            # maybe do some checking of the file name here
            #self.newstatus("New file name is %s" % dialog.get_filename())
            self.database.filename = dialog.get_filename()
            self.internFileSave()

        elif response == gtk.RESPONSE_CANCEL:
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
        dialog = gtk.FileChooserDialog(title="Save waveform as...",
                                       action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                       buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_SAVE,
                                                gtk.RESPONSE_OK))
        dialog.set_current_name(self.database.filename.replace('.csv', '.wfm'))
            
        dialog.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("WFM files")
        filter.add_pattern("*.wfm")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_CANCEL:
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
        editwindow = gtk.Window()
        editwindow.set_title("Vehicle Preferences")
        #editwindow.set_size_request(400,300)

        table = gtk.Table(len(vehPrefFields) + 1, 2, False)
        
        for x in range(0, len(vehPrefFields)):
            field = vehPrefFields[x]
            label = gtk.Label(field)
            table.attach(label, 0, 1, x, x + 1)

            entry = gtk.Entry()
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
        if (not VehProperties.has_key(field) or entry.get_text() != VehProperties[field]):
            self.makeDirty()

            VehProperties[field] = entry.get_text()

            # redraw main window here
            self.newstatus("Updated %s property" % field)
    	
    	return
    
    def propWindowEntryFocusOut(self, widget, event, field):
    	# this basically throws out the 'event'
        return self.updateProperty(widget, field)

    def menuEditPreferences(self, widget):
        editwindow = gtk.Window()
        editwindow.set_title("User Preferences")

        table = gtk.Table(len(UserPreferences) + 1, 2, False)
        
        for x in range(0, len(UserPreferences)):
            field = UserPreferences.keys()[x]
            label = gtk.Label(field)
            table.attach(label, 0, 1, x, x + 1)

            entry = gtk.Entry()

            entry.set_text(UserPreferences[field])

            entry.connect("activate", self.updatePreference, field)
            entry.connect("focus-out-event", self.prefWindowEntryFocusOut, field)
            table.attach(entry, 1, 2, x, x + 1)

        editwindow.add(table)
        
        editwindow.show_all()
        self.newstatus("Opened window to edit preferences")
        
    	return

    
    def updatePreference(self, entry, field):
        if (entry.get_text() != UserPreferences[field]):
            self.makeDirty()

            UserPreferences[field] = entry.get_text()

            # redraw main window here
            self.newstatus("Updated %s preference" % field)
    	
    	return
    
    def prefWindowEntryFocusOut(self, widget, event, field):
    	# this basically throws out the 'event'
        return self.updatePreference(widget, field)

    def menuEditDel(self, widget):
        # ask user if they're sure when I learn how

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
        return (self.gnuplot_p != False and self.gnuplot_p.poll() == None)

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
            'dpd': 'Fuel Cost per Day',
            }
        ylabels = {'mpd': 'Miles per Day [mi/day]',
            'mpg': 'Miles per Gallon [mi/gal]',
            'dpg': 'Dollars per Gallon [$/gal]',
            'dpd': 'Dollars per Day [$/day]',
            }

        commands = [
            "set term %s" % UserPreferences['GnuPlotTerm'], # having trouble with default 'aqua' on Mac OSX
            "set xdata time",
            "set timefmt '%s'",
            #"set xtics rotate by 90",
            "set xtics nomirror rotate by -75",
            "set autoscale",
            "set log y" if (field == "mpd" or field == "dpd") else "unset log",
            "unset key",
            "set grid",

            "set title '%s'" % titles[field],
            "set xlabel 'Date'",
            "set ylabel '%s'" % ylabels[field],
            # the %s here allows me to annotate a point with a string
            "plot '-' using 1:2 with lines%s" % self.gnuplot_annot,
            ]

        if (not self.isPlotActive()):
            print UserPreferences['GnuPlotPath']
            self.gnuplot_p = subprocess.Popen(
                UserPreferences['GnuPlotPath'], shell=True,
                stdin=subprocess.PIPE,
                #stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
                )
            #gnuplot_in = open('gnuplot.in', 'w')
            #print self.gnuplot_p.stdout.readline()

        for cmd in commands:
            if (self.gnuplot_p.poll() != None):
                print "GNUPLOT terminated."
                return

            #print >> gnuplot_in, cmd
            self.gnuplot_p.stdin.write(cmd + "\n")


        #oldestDate = int(time.mktime(self.database[-1][storedFields.index('date')].timetuple())) - 31557600.0 #6*(52.0/12)*7*24*3600
        oldestDate = mktimestamp(self.database[-1].date) - 31557600.0 #6*(52.0/12)*7*24*3600
        print "Date range: " + fmttimestamp(oldestDate) + " to now"
	# DONE make this [storedFields.index('whatever')] into .whatever
	# TODO make function for time.mktime(time).timetuple()
        #print self.gnuplot_p.communicate()
        #print self.gnuplot_p.stdout.read()

        # write each of the records to the pipe
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
        dialog = gtk.FileChooserDialog(title="Save plot as...", action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_current_name(self.database.filename.replace('.csv', '.ps'))
            
        dialog.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("PostScript files")
        filter.add_pattern("*.ps")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_CANCEL:
            self.newstatus('No file selected')
            dialog.destroy()
            return

        plotFileName = dialog.get_filename()
        dialog.destroy()

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
        # Open up a single 'new record' window, if it doesn't already exist
        # Have 'Save' and 'Cancel' buttons at the bottom
        # Don't modify self until 'Save'

        newrow = ["", datetime.date.today().strftime(dateFmtStr), "", "", "", "", True, ""]
        
        self.editwindow = gtk.Window()
        self.editwindow.set_title("Create New Record")

        table = gtk.Table(len(storedFields) + 1, 2, False)
        self.newRecordEntries = []
        for x in range(0, len(storedFields)):
            label = gtk.Label(storedFieldLabels[x])
            table.attach(label, 0, 1, x, x + 1)

            if (storedFields[x] == 'fill'):
                button = gtk.CheckButton(storedFieldLabels[x])
                button.set_active(True)
                #button.connect("clicked", self.updateBool, newrownum, x)
                table.attach(button, 1, 2, x, x + 1)
                self.newRecordEntries.append(button)
            else:
                entry = gtk.Entry()
                entry.set_text(newrow[x])
                #entry.connect("activate", self.updateField, newrownum, x)
                table.attach(entry, 1, 2, x, x + 1)
                self.newRecordEntries.append(entry)

        bbox = gtk.HButtonBox()
        save_button = gtk.Button(label="Save", stock=gtk.STOCK_OK)
        save_button.connect("activate", self.saveNewRecord)
        save_button.connect("clicked", self.saveNewRecord)
        bbox.add(save_button)
        canc_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        canc_button.connect("activate", self.closeEditWindow)
        canc_button.connect("clicked", self.closeEditWindow) # TODO FIXME this doesn't work: TypeError: destroy() takes no arguments (1 given)
        bbox.add(canc_button)
        bbox.set_spacing(20)
        bbox.set_layout(gtk.BUTTONBOX_SPREAD)

        vbox = gtk.VBox(False, 0)
        vbox.pack_start(table, False, False, 0)
        vbox.pack_end(bbox, False, False, 0)

        self.editwindow.add(vbox)
        self.editwindow.show_all()

        return

    def saveNewRecord(self, widget):
        newrownum = len(self.database.recordTable)
        newrow = dict()

        try:
            for x in range(0, len(storedFields)):
                if (storedFields[x] == 'fill'):
                    newrow[storedFields[x]] = "Yes" if self.newRecordEntries[x].get_active() else "No"
                else:
                    if (storedFields[x] in ['odo', 'gals', 'dpg'] 
                        and self.newRecordEntries[x].get_text() == ""):
                        raise NameError('Missing required field')
                    newrow[storedFields[x]] = self.newRecordEntries[x].get_text()
			#FuelRecord.formatText(
                        #storedFields[x],
                        #self.newRecordEntries[x].get_text())
                    
            # want to do a check here for the date being wrong
            # records are sorted by odometer, need to make sure this record isn't before the previous or after the next 
        except ValueError:
            self.show_error('Invalid format, try again.')
        except NameError:
            self.show_error('You left a required field blank.')
        else:

            # If entries OK
            self.makeDirty()
            self.database.addNewRecord(FuelRecord(newrow))
            self.updateList()
            self.updatePlot()
            self.newstatus("New record created.")
            self.editwindow.destroy()

        return
    
    def updateList(self):
        self.recordList = gtk.ListStore(object)
# TODO improve sorting flexibility here 
        for i in range(len(self.database.recordTable) - 1, -1, -1):
        #for i in range(0, len(self.database.recordTable)):
            self.recordList.append([i])
        self.treeview.set_model(self.recordList)
        
        return

    def closeEditWindow(self, widget):
        self.editwindow.destroy
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
        about = gtk.AboutDialog()
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
        summaryWindow = gtk.Window()
        summaryWindow.set_title("Summary")

        tableLabels = self.database.getSummaryTable()

	numRows = len(tableLabels)/3

        table = gtk.Table(numRows, 2, False)
        for i in range(0, numRows):
            myLabel = gtk.Label(tableLabels[3 * i])
            myLabel.set_alignment(0, 0.5)
            table.attach(myLabel, 1, 2, i, i + 1, ypadding=4, xpadding=8)

            myLabel = gtk.Label(tableLabels[3 * i + 1])
            myLabel.set_alignment(1, 0.5)
            table.attach(myLabel, 2, 3, i, i + 1, ypadding=4, xpadding=8)

            myLabel = gtk.Label(tableLabels[3 * i + 2])
            myLabel.set_alignment(0, 0.5)
            table.attach(myLabel, 3, 4, i, i + 1, ypadding=4, xpadding=8)

            # Dump to terminal too (makes easy copy & paste)
            print tableLabels[3 * i], "\t", tableLabels[3 * i + 1], "\t", tableLabels[3 * i + 2]

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
        self.makeDirty()
        self.database[window.row][col] = button.get_active()
        self.newstatus("Set %s to %s on record %d" % 
                       (storedFieldLabels[col],
                        "Yes" if button.get_active() else "No", window.row)
                       )
        self.window.queue_draw()
        return

    def updateField(self, entry, editwindow, col):
        if (entry.get_text() != self.database.getText(editwindow.row, storedFields[col])):
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
                        editwindow.update()
                        self.newstatus("Warning: You have changed the position of the record to %d" % (newrow+1))
    
                # redraw main window here
                self.newstatus("Updated %s on record %d" % (storedFieldLabels[col], (editwindow.row+1)))
                self.window.queue_draw()
                self.updatePlot()
                
            except ValueError:
                print 'Caught ValueError'
                self.show_error('Invalid format, try again.')

        return

    def show_error (self, string):
        md = gtk.MessageDialog(None,
            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
            gtk.BUTTONS_CLOSE, string)
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
                file_basename,
                "*" if self.database.dirty_bit else ""))
        return

    def on_status_view(self, widget):
        if widget.active: 
            self.statusbar.show()
        else:
            self.statusbar.hide()


gui = PyMPG()
#gui.window.destroy()
gtk.main()
