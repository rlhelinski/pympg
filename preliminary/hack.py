#!/usr/bin/python

# ZetCode PyGTK tutorial 
#
# This example shows a menu with
# images, accelerators and a separator
#
# author: jan bodnar
# website: zetcode.com 
# last edited: February 2009

import gtk
import csv
import time
import datetime

class PyMPG:
    recordTable = []
    #columnNames = ['Date', 'Days', 'Odo.', 'Dist.', 'Gals', '$/gal', 'Cost', 'mi/day', 'Location', 'Station', 'Fill?', 'mi/gal']
    columnNames = ['Date', 'Odo.', 'Gals', '$/gal', 'Location', 'Station', 'Fill?', 'Comment']

    def __init__(self, dname = None):
        #super(PyApp, self).__init__()

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("PyMPG")
        self.window.set_size_request(400, 300)
        #self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(6400, 6400, 6440))
        self.window.set_position(gtk.WIN_POS_CENTER)

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
        newi.add_accelerator("activate", agr, key, 
            mod, gtk.ACCEL_VISIBLE)
        filemenu.append(newi)

        openm = gtk.ImageMenuItem(gtk.STOCK_OPEN, agr)
        key, mod = gtk.accelerator_parse("O")
        openm.add_accelerator("activate", agr, key, 
            mod, gtk.ACCEL_VISIBLE)
        openm.connect("activate", self.openfile)
        filemenu.append(openm)

        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)

        exit = gtk.ImageMenuItem(gtk.STOCK_QUIT, agr)
        key, mod = gtk.accelerator_parse("Q")
        exit.add_accelerator("activate", agr, key, 
            mod, gtk.ACCEL_VISIBLE)

        exit.connect("activate", gtk.main_quit)
        filemenu.append(exit)

        # View menu
        viewmenu = gtk.Menu()
        view = gtk.MenuItem("View")
        view.set_submenu(viewmenu)

        statm = gtk.MenuItem("Show Statistics")
        #key, mod = gtk.accelerator_parse("T")
        #statm.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        statm.connect("activate", self.showstats)
        viewmenu.append(statm)

        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)

        stat = gtk.CheckMenuItem("Show Statusbar")
        stat.set_active(True)
        stat.connect("activate", self.on_status_view)
        viewmenu.append(stat)
        
        mb.append(filem)
        mb.append(view)

        self.statusbar = gtk.Statusbar()
        self.statusbar.push(1, "Ready")

        vbox = gtk.VBox(False, 2)
        vbox.pack_start(mb, False, False, 0)
        #vbox.pack_start(gtk.Label(), True, False, 0)

        # create the TreeView
        self.treeview = gtk.TreeView()
        cell_data_funcs = (self.format_date, self.format_odo, self.format_gals, self.format_dpg, self.format_location, self.format_station, self.format_fill, self.format_comment)

 
        # create the TreeViewColumns to display the data
        self.tvcolumn = [None] * len(self.columnNames)
        #cellpb = gtk.CellRendererPixbuf()
        #self.tvcolumn[0] = gtk.TreeViewColumn(self.columnNames[0], cellpb)
        #self.tvcolumn[0].set_cell_data_func(cellpb, self.file_pixbuf)
        #cell = gtk.CellRendererText()
        #self.tvcolumn[0].pack_start(cell, False)
        #self.tvcolumn[0].set_cell_data_func(cell, self.file_name)
        #self.treeview.append_column(self.tvcolumn[0])
        for n in range(0, len(self.columnNames)):
            cell = gtk.CellRendererText()
            self.tvcolumn[n] = gtk.TreeViewColumn(self.columnNames[n], cell)
#            if n == 1:
#                cell.set_property('xalign', 1.0)
            self.tvcolumn[n].set_cell_data_func(cell, cell_data_funcs[n])
            self.treeview.append_column(self.tvcolumn[n])

        # Might pop up the comment here
        #self.treeview.connect('row-activated', self.open_file)
        self.scrolledwindow = gtk.ScrolledWindow()
        self.scrolledwindow.add(self.treeview)
        vbox.pack_start(self.scrolledwindow, True, True, 0)
        #self.window.add(self.scrolledwindow)

        vbox.pack_start(self.statusbar, False, False, 0)
        self.window.add(vbox);
#        self.treeview.set_model(listmodel)



        self.window.connect("destroy", gtk.main_quit)
        self.window.show_all()

    def newstatus(self, string):
        self.statusbar.pop(1)
        self.statusbar.push(1, string)
        
    def openfile(self, widget):
        dialog = gtk.FileChooserDialog("Choose file", None, gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                       gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
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
          self.loadfile(dialog.get_filename())
        elif response == gtk.RESPONSE_CANCEL:
          print 'Closed, no files selected'
        dialog.destroy()

    def loadfile(self, filename):
          # Load records from CSV file
          fileReader = csv.reader(open(filename), delimiter=',', quotechar='"')
          recordList = gtk.ListStore(object)
          i = 0
          for row in fileReader:
              print len(row), ', '.join(row)
              self.recordTable.append(row)
              #self.recordList.append(row)
              recordList.append([i])
              i = i + 1

          print filename, 'loaded.'

          # Load new interface
          self.treeview.set_model(recordList)

          self.newstatus(filename + " loaded"  )

    def format_date(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        record = self.recordTable[row][0]
        date = time.strptime(record, "%m/%d/%Y")
        cell.set_property('text', time.strftime("%Y/%m/%d", date))
        return 

    def format_odo(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.recordTable[row][1])
        return 

    def format_gals(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.recordTable[row][2])
        return 

    def format_dpg(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.recordTable[row][3])
        return 

    def format_location(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.recordTable[row][4])
        return 

    def format_station(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.recordTable[row][5])
        return 

    def format_fill(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.recordTable[row][6])
        return 


    def format_comment(self, column, cell, model, iter):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.recordTable[row][7])
        return 

    def showstats(self, widget):

        return

    def on_status_view(self, widget):
        if widget.active: 
            self.statusbar.show()
        else:
            self.statusbar.hide()


PyMPG()
gtk.main()

