#!/usr/bin/python

# PyMPG - Python Mileage Processing GUI
#
# Need to:
# implement export to GNUPLOT waveform
# change format_* functions to call getText(), maybe at the original call level?
# 
# History:
# add derived fields but not store them anywhere (neat) DONE
# implement file save function DONE
# implement summary window DONE
# implement add new record dialog DONE
# implement delete record DONE
# implement edit record dialog DONE
# fixed old file remaining on open or new file action
# fixed accelerator keys
# fixed menu items not being disabled (new record when no file open)
# implement new file function DONE
# add about dialog DONE
# implement dirty_bit for tracking if file is modified DONE
# create function for setting the main window title DONE
# disable 'save' until dirty_bit -> 1 DONE
# 

import sys
import gtk
import csv
import time
import datetime
#from datetime import datetime, date, time
import traceback
import string
import subprocess

progname = "PyMPG"
progver = "0.2"
progcopy = "Copyleft Ryan Helinski"
progcomm = "A simple tool for keeping track of gas mileage."
progurl = "http://pgmdb.sf.net/"

invalidStr = "--"
dateFmtStr = "%Y/%m/%d"

pumpxpm = [
    "128 128 17 1",
    " 	c None",
    ".	c #231F1E",
    "+	c #302C2B",
    "@	c #383433",
    "#	c #4C4847",
    "$	c #5A5554",
    "%	c #6C6766",
    "&	c #787372",
    "*	c #898482",
    "=	c #999392",
    "-	c #AAA4A3",
    ";	c #B8B2B1",
    ">	c #CEC9C8",
    ",	c #DCDCDA",
    "'	c #E8E7E5",
    ")	c #F4F6F3",
    "!	c #FEFFFC",
    "           ...........................................................................................................          ",
    "         ...............................................................................................................        ",
    "       .....@&=-;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;=&#.....      ",
    "      ....&,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'*....     ",
    "     ...@;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!>#...    ",
    "    ...%'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!)*...   ",
    "   ...&!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!=...  ",
    "   ..@)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!$... ",
    "  ...>!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!,+.. ",
    "  ..*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!-.. ",
    " ...)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!@..",
    " ..$!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!&..",
    " ..=!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!;..",
    " ..;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!,..",
    " ..>!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!)..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!';*%%%%%%%%%%%%%%%%%%%%%%%&->)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'%.............................+-!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!;@................................$'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!,+..................................%!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!$....................................;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....................................@!!!!!!!!!!)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*.....@=>>>>>>>>>>>>>>>>>>>>>>>>&......,!!!!!!!)=+;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!$.....;!!!!!!!!!!!!!!!!!!!!!!!!!!%.....;!!!!!!'#...;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!@....+!!!!!!!!!!!!!!!!!!!!!!!!!!!-.....*!!!!!!*.....;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....*!!!!!!)#.....;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....*!!!!!!!'@.....;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....*!!!!!!!!>......;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....*!!!!!!!!!-......;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!=......;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!=......;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!*......;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!>.......;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!>........-!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!;.........-!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!;..........>!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!;..........#)!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!;...........*!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!;...#';$.....,!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!-...#!!)$....;!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!-...#!!!-....*!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....=!!!!!!!!!!!!-...#!!!>....$!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....-!!!!!!!!!!!!-...#!!!,....@!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....+!!!!!!!!!!!!!!!!!!!!!!!!!!!;.....-!!!!!!!!!!!!;...+)!!,....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+.....'!!!!!!!!!!!!!!!!!!!!!!!!!!*.....;!!!!!!!!!!!!'....=!!,....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+.....&)!!!!!!!!!!!!!!!!!!!!!!!!,@.....;!!!!!!!!!!!!!@...+;!,....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......+$$$$$$$$$$$$$$$$$$$$$$$#.......>!!!!!!!!!!!!!>.....@%....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................>!!!!!!!!!!!!!!&..........+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................>!!!!!!!!!!!!!!!=+........+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................,!!!!!!!!!!!!!!!!,*$@.....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................'!!!!!!!!!!!!!!!!!!!!!*...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................'!!!!!!!!!!!!!!!!!!!!!*...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................)!!!!!!!!!!!!!!!!!!!!!&...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................!!!!!!!!!!!!!!!!!!!!!!&...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+.....................................+!!!!!!!!!!!!!!!!!!!!!!%...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................########%=>)!!!!!!!!!!%...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+.................................................#>!!!!!!!!!$...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+...................................................*!!!!!!!!$...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....................................................;!!!!!!!$...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+....................................................+'!!!!!!#...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................$=======%......*!!!!!!#...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!'#....$!!!!!!@...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!;.....!!!!!!@...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!+....,!!!!!+...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!+...+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!)....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!)....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!'....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!'....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!,....+!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!'.....!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!.....'!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!@....>!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!$....;!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!&....=!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!*....&!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!-....$!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!>....+!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!'.....'!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!@....;!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!%....=!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!*....&!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!;....#!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!,.....)!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!+....,!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!$....;!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!&....*!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!-....%!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!>....@!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!).....)!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!#....>!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!%....-!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!=....*!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!>....$!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!'....@!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!!@....'!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!!$....>!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....,!!!!!!!!!*....=!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....'!!!!!!!!!;....&!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!@....'!!!!!!!!!-....$!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!$....>!!!!!!!!!&....#!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!*....*!!!!!!!!'@....%!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!;.....>!!!!!!!$.....-!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!'+....+=!!!!>#.....+)!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!!-......@$%#.......;!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!!!%...............=!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!!!)#.............&!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!+......................................*!!!!!!!!!!!!!!=..........#>!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!=**&&&&%%%%$$$$$####@@@@++.............*!!!!!!!!!!!!!!!,%@.....#-!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!)))''',,,'!!!!!!!!!!!!!!!!!!';;,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!..",
    " ..>!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'..",
    " ..-!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!>..",
    " ..*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!-..",
    " ..@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!$..",
    " ...>!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'...",
    "  ..#)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!$.. ",
    "  ...*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!-... ",
    "   ...>!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'+..  ",
    "    ..#,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'$...  ",
    "    ...+=!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!;@...   ",
    "     ....$,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'%....    ",
    "       ...+&;)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!)>&@....     ",
    "        ......+###################################################################################################+......       ",
    "          .............................................................................................................         ",
    "             .......................................................................................................            "
    ]
pumppb = gtk.gdk.pixbuf_new_from_xpm_data(pumpxpm)


class PyMPG:
    recordTable = []
    storedFields = ['date', 'odo', 'gals', 'dpg', 'location', 'station', 'fill', 'comment']
    storedFieldLabels = ['Date', 'Odometer', 'Gallons', 'Price / Gal', 'Location', 'Station', 'Filled?', 'Comment']

    fullFields = ['date', 'days', 'odo', 'dist', 'gals', 'dpg', 'tankcost', 'mpd', 'station', 'location', 'fill', 'mpg', 'comment']
    columnNames = ['Date', 'Days', 'Odo.', 'Dist.', 'Gals', '$/gal', 'Cost', 'mi/day', 'Station', 'Location', 'Fill?', 'mi/gal', 'Comment']
    #columnNames = ['Date', 'Odo.', 'Gals', '$/gal', 'Location', 'Station', 'Fill?', 'Comment']

    filename = ""
    dirty_bit = False
    gnuplot_p = False

    def __init__(self, dname = None):
        #super(PyApp, self).__init__()

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(progname)
        self.window.set_size_request(800, 600)
        #self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(6400, 6400, 6440))
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_icon(pumppb)
        #self.window.connect("activate-default", self.windowActivate)

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
        openm.add_accelerator("activate", agr, key, 
            mod, gtk.ACCEL_VISIBLE)
        openm.connect("activate", self.openfile)
        filemenu.append(openm)

        self.savem = gtk.ImageMenuItem(gtk.STOCK_SAVE, agr)
        key, mod = gtk.accelerator_parse("S")
        self.savem.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        self.savem.set_sensitive(False)
        self.savem.connect("activate", self.menuFileSave)
        filemenu.append(self.savem)

        # Seperator here?
        self.exportm = gtk.MenuItem("Export Waveform")
        self.exportm.set_sensitive(False)
        self.exportm.connect("activate", self.menuFileExport)
        filemenu.append(self.exportm)

        sep = gtk.SeparatorMenuItem()
        filemenu.append(sep)

        exit = gtk.ImageMenuItem(gtk.STOCK_QUIT, agr)
        key, mod = gtk.accelerator_parse("Q")
        exit.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        exit.connect("activate", gtk.main_quit)
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

        self.plotmpdm = gtk.MenuItem("Miles/Day")
        self.plotmpdm.connect("activate", self.menuPlot, 'mpd')
        plotmenu.append(self.plotmpdm)

        self.plotmpgm = gtk.MenuItem("Miles/Gal")
        self.plotmpgm.connect("activate", self.menuPlot, 'mpg')
        plotmenu.append(self.plotmpgm)

        self.plotdpgm = gtk.MenuItem("Dollars/Gal")
        self.plotdpgm.connect("activate", self.menuPlot, 'dpg')
        plotmenu.append(self.plotdpgm)

        mb.append(self.plot)

        # Help menu
	helpmenu = gtk.Menu()
	help = gtk.MenuItem("Help")
	help.set_submenu(helpmenu)

	aboutm = gtk.MenuItem("About")
	aboutm.connect("activate", self.openAboutWindow)
	helpmenu.append(aboutm)

	mb.append(help)

	# Main window guts

        self.statusbar = gtk.Statusbar()
        self.statusbar.push(1, "Ready")

        vbox = gtk.VBox(False, 2)
        vbox.pack_start(mb, False, False, 0)
        #vbox.pack_start(gtk.Label(), True, False, 0)

        # create the TreeView
        self.treeview = gtk.TreeView()
        self.treeview.set_headers_clickable(True)

        # create the TreeViewColumns to display the data
        self.tvcolumn = [None] * len(self.columnNames)
        for n in range(0, len(self.columnNames)):
            cell = gtk.CellRendererText()
            self.tvcolumn[n] = gtk.TreeViewColumn(self.columnNames[n], cell)
#            if n == 1:
#                cell.set_property('xalign', 1.0)
            self.tvcolumn[n].set_cell_data_func(cell, self.format_comment, self.fullFields[n])
            self.treeview.append_column(self.tvcolumn[n])

        self.treeview.connect('row-activated', self.editrecord)
        self.treeview.connect('cursor-changed', self.on_row_select)
        self.scrolledwindow = gtk.ScrolledWindow()
        self.scrolledwindow.add(self.treeview)
        vbox.pack_start(self.scrolledwindow, True, True, 0)

        vbox.pack_start(self.statusbar, False, False, 0)
        self.window.add(vbox)

        self.window.connect("destroy", gtk.main_quit)
        self.window.show_all()

        if (len(sys.argv) > 1):
            self.loadfile(sys.argv[1])

    def newstatus(self, string):
        self.statusbar.pop(1)
        print string
        self.statusbar.push(1, string)

    def on_row_select(self, widget):
        model, iter = self.treeview.get_selection().get_selected()
        row = model.get_value(iter, 0)
        #print "Row", row, "selected" 
        self.modifym.set_sensitive(True)
        self.deletem.set_sensitive(True)
        return

    def on_file_loaded(self):
        self.savem.set_sensitive(True)
        self.exportm.set_sensitive(True)
        self.recordm.set_sensitive(True)
        self.modifym.set_sensitive(True)
        self.deletem.set_sensitive(True)
        self.summarym.set_sensitive(True)
        self.plot.set_sensitive(True)
        return

    def menuFileNew(self, widget):
        self.newfile()
        return

    def newfile(self):
        self.recordTable = []
        self.recordList = gtk.ListStore(object)
        self.filename = ""

        # Load new interface
        self.makeClean()
        self.on_file_loaded()
        self.treeview.set_model(self.recordList)
        self.newstatus("New file created")
        return
        
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
          self.newstatus('No file selected')
        dialog.destroy()
        return

    def loadfile(self, filename):
          # Load records from CSV file
          self.recordTable = []
          self.recordList = gtk.ListStore(object)
          fileReader = csv.reader(open(filename), delimiter=',', quotechar='"')
          i = 0
          for row in fileReader:
              if (len(row) != 8):
                  raise NameError('Wrong number of fields in CSV file!')

              #print len(row), ', '.join(row)
              # data pre-processing / input error checking
              # convert date string to time struct
              row[0] = datetime.datetime(*time.strptime(row[0], dateFmtStr)[0:5]) 
              row[1] = int(row[1]) # convert odo to int
              row[2] = float(row[2]) # convert gals to float
              row[3] = float(row[3]) # convert $/gal to float
              row[6] = (row[6] == "Yes")

              self.recordTable.append(row)
              #self.recordList.append(row)
              self.recordList.append([i])
              i = i + 1

          #self.window.set_title("%s - %s" % (progname, filename))
          self.filename = filename # Save file name for later

          # Load new interface
          self.makeClean()
          self.on_file_loaded()
          self.treeview.set_model(self.recordList)
          self.newstatus(filename + " loaded")
          return

    def menuFileSave(self, widget):
        # check that a filename is set
        if ( self.filename == "" ):
            dialog = gtk.FileChooserDialog(title="Choose file name...",action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
            
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
                # maybe do some checking of the file name here
                self.newstatus("New file name is %s" % dialog.get_filename())
            elif response == gtk.RESPONSE_CANCEL:
                self.newstatus('No file selected')
                dialog.destroy()
                return
            self.filename = dialog.get_filename()
            dialog.destroy()

        # save the file that is open
        self.saveFile(self.filename)
        return

    def menuFileExport(self, widget):
        dialog = gtk.FileChooserDialog(title="Save waveform as...",action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        dialog.set_current_name(self.filename.replace('.csv', '.wfm'))
            
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
        self.exportWaveform(filename)

        return

    def menuEditDel(self, widget):
        # ask user if they're sure when I learn how

        model, iter = self.treeview.get_selection().get_selected()
        row = model.get_value(iter, 0)
        self.deleteRecord(row)
        return

    def menuViewSummary(self, widget):
        self.createSummaryWindow()
        return

    def editmenumodify(self, widget):
        model, iter = self.treeview.get_selection().get_selected()
        row = model.get_value(iter, 0)
        self.createEditWindow(row)
        return

    def saveFile(self, filename):
        # Save records back to a CSV file
        fileWriter = csv.writer(open(filename, 'w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

        i = 0
        for i in range(0, len(self.recordTable)):
            j = 0
            textrow = []
            for j in range(0, len(self.storedFields)):
                textrow.append(self.getText(i, self.storedFields[j]))
            fileWriter.writerow(textrow)

        self.makeClean()
        #self.window.set_title("%s - %s" % (progname, filename))
        self.newstatus("File %s saved." % filename)
        return

    def exportWaveform(self, filename):
        waveform = self.createWaveform()
        wfmfile = open(filename, 'w')
        wfmfile.write(waveform)
        wfmfile.close()

        self.newstatus('Exported waveform to %s' % filename)
        return

    def createWaveform(self):
        # Need a function here for later piping with GNUPLOT
        skipFields = ["station", "location", "fill", "comment"]
        # TODO Replace skipfields with wfmcols
        wfmcols = ['date', 'days', 'odo', 'dist', 'gals', 'dpg', 'tankcost', 'mpd', 'mpg']

        # Write a header comment to label the columns
        wfm = "# "
        for x in range(0, len(self.fullFields)):
            if (self.fullFields[x] in skipFields):
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
            for y in range(0, len(self.fullFields)):
                if (self.fullFields[y] == 'date'):
                    # Convert the datetime obj to Epoch seconds
                    line += "%d" % time.mktime( self.recordTable[x][self.storedFields.index('date')].timetuple() )
                elif (self.fullFields[y] in skipFields):
                    # Skip these, they're not useful for plotting
                    pass
                else:
                    line += "\t" + self.getText(x,self.fullFields[y]) 

            # Make certain sequences GNUPLOT-friendly
            line = line.replace('*', '')
            line = line.replace(invalidStr, '0')
            wfm += line + "\n"

        return wfm

    def menuPlot(self, widget, field):
        self.plotData(field)
        return

    def plotData(self, field):
        titles = {'mpd': 'Mileage',
            'mpg': 'Fuel Economy',
            'dpg': 'Fuel Price',
            }
        ylabels = {'mpd': 'Miles per Day [mi/day]',
            'mpg': 'Miles per Gallon [mi/gal]',
            'dpg': 'Dollars per Gallon [$/gal]',
            }

        commands = [
            "set xdata time",
            "set timefmt '%s'",
            "set xtics rotate by 90",
            "set autoscale",
            "unset key",
            "set grid",

            "set title '%s'" % titles[field],
            "set xlabel 'Date' 0,-1",
            "set ylabel '%s'" % ylabels[field],
            "plot '-' using 1:2 with lines",
            ]

        if (self.gnuplot_p == False or self.gnuplot_p.poll() == 0):
            self.gnuplot_p = subprocess.Popen('/usr/bin/gnuplot', shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                )

        for cmd in commands:
            if (self.gnuplot_p.poll() == 0):
                print "Child terminated."
                break

            self.gnuplot_p.stdin.write(cmd + "\n")

        for x in range(0, len(self.recordTable)):
            # Convert the datetime obj to Epoch seconds
            secs = "%d" % time.mktime( self.recordTable[x][self.storedFields.index('date')].timetuple() )
            self.gnuplot_p.stdin.write(secs + "\t" + self.getText(x, field) + "\n")
        self.gnuplot_p.stdin.write("e\n")

        #self.gnuplot_p.wait()
        self.newstatus("Generated %s plot." % titles[field])

        return

    def getText(self, row, field):
        if (field in self.storedFields):
            col = self.storedFields.index(field)

        odoi = self.storedFields.index("odo")
        datei = self.storedFields.index("date")
        galsi = self.storedFields.index("gals")
        filli = self.storedFields.index("fill")
        dpgi = self.storedFields.index("dpg")

        if (field == "date"):
            return self.recordTable[row][col].strftime(dateFmtStr)
            #return datetime.strftime(dateFmtStr,self.recordTable[row][col])
        elif (field == "days"):
            if (row == 0):
                return invalidStr

            timedelta = self.recordTable[row][datei] - self.recordTable[row-1][datei]
            return "%d" % timedelta.days
        elif (field == "dist"):
            if (row == 0):
                return invalidStr

            return "%d" % (self.recordTable[row][odoi] - self.recordTable[row-1][odoi])
        elif (field == "tankcost"):
            cost = self.recordTable[row][galsi] * self.recordTable[row][dpgi]
            return "%.2f" % cost

        elif (field == "mpd"):
            if (row == 0):
                return invalidStr

            dist = self.recordTable[row][odoi] - self.recordTable[row-1][odoi]
            timedelta = self.recordTable[row][datei] - self.recordTable[row-1][datei]
            days = timedelta.days
            if (days == 0):
                mpd = dist
            else:
                mpd = dist / days

            return "%d" % mpd

        elif (field == "mpg"):
            if (row == 0):
                return invalidStr
            else:
                dist = self.recordTable[row][odoi] - self.recordTable[row-1][odoi]
                gals = self.recordTable[row][galsi]
                mpg = "%0.1f" % (dist / gals)
                return mpg + ("" if (self.recordTable[row][filli]) else "*")
            
        elif (field == "fill"):
            return "Yes" if self.recordTable[row][col] else "No"
        else:
            return "%s" % self.recordTable[row][col]

    def setText(self, row, field, text):
        col = self.storedFields.index(field)
        #print field, col
        self.recordTable[row][col] = self.checkText(field, text)

        return

    def checkText(self, field, text):
        if (field == "date"):
            retval = datetime.strptime(text, dateFmtStr)
        elif (field == "odo"):
            retval = int(text)
        elif (field == "gals"):
            retval = round(float(text), 3)
        elif (field == "dpg"):
            retval = round(float(text), 3)
        else:
            retval = text

        return retval

    def newrecord(self, widget):
        # Open up a single 'new record' window, if it doesn't already exist
        # Have 'Save' and 'Cancel' buttons at the bottom
        # Don't modify self until 'Save'

        newrow = [datetime.date.today().strftime(dateFmtStr), "", "", "", "", "", True, ""]
        
        self.editwindow = gtk.Window()
        self.editwindow.set_title("Create New Record")
        #editwindow.set_size_request(320,240)

        table = gtk.Table(len(self.storedFields)+1, 2, False)
        self.newRecordEntries = []
        for x in range(0, len(self.storedFields)):
            label = gtk.Label(self.storedFieldLabels[x])
            table.attach(label, 0, 1, x, x+1)

            if (self.storedFields[x] == 'fill'):
                button = gtk.CheckButton(self.storedFieldLabels[x])
                button.set_active(True)
                #button.connect("clicked", self.updateBool, newrownum, x)
                table.attach(button, 1, 2, x, x+1)
                self.newRecordEntries.append(button)
            else:
                entry = gtk.Entry()
                entry.set_text(newrow[x])
                #entry.connect("activate", self.updateField, newrownum, x)
                table.attach(entry, 1, 2, x, x+1)
                self.newRecordEntries.append(entry)

        bbox = gtk.HButtonBox()
        save_button = gtk.Button(label="Save", stock=gtk.STOCK_OK)
        #self.editwindow.connect("destroy", self.saveNewRecord)
        save_button.connect("activate", self.saveNewRecord)
        save_button.connect("clicked", self.saveNewRecord)
        bbox.add(save_button)
        canc_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        canc_button.connect("activate", self.closeNewWindow)
        canc_button.connect("clicked", self.closeNewWindow)
        bbox.add(canc_button)
        bbox.set_spacing(20)
        bbox.set_layout(gtk.BUTTONBOX_SPREAD)

        vbox = gtk.VBox(False, 0)
        vbox.pack_start(table, False, False, 0)
        vbox.pack_end(bbox, False, False, 0)

        self.editwindow.add(vbox)
        #self.editwindow.connect("destroy", self.saveNewRecord)
        self.editwindow.show_all()

        return

    def closeNewWindow(self, widget):
        self.editwindow.destroy()
        return

    def saveNewRecord(self, widget):
        newrownum = len(self.recordTable)
        newrow = []

        try:
            for x in range(0, len(self.storedFields)):
                if (self.storedFields[x] == 'fill'):
                    newrow.append(self.newRecordEntries[x].get_active())
                else:
                    if (self.storedFields[x] in ['odo', 'gals', 'dpg'] and self.newRecordEntries[x].get_text() == ""):
                        raise NameError('Missing required field')
                    newrow.append(self.checkText(self.storedFields[x],self.newRecordEntries[x].get_text()))
        except ValueError:
            self.show_error('Invalid format, try again.')
        except NameError:
            self.show_error('You left a required field blank.')
        else:

            # If entries OK
            self.makeDirty()
            self.recordTable.append(newrow)
            self.recordList.append([len(self.recordTable) - 1])
            self.treeview.set_model(self.recordList)
            self.newstatus("New record created.")
            self.editwindow.destroy()

        return

    def deleteRecord(self, row):
        del self.recordTable[row]
        del self.recordList[row]
        self.makeDirty()
        self.newstatus("Deleted record %d" % row)
        return

    def editrecord(self, tree, path, column):
        #editdialog = gtk.Dialog(title="Edit Record", parent=self.window)
        #row = model.get_value(iter, 0)
        #print self, tree, path, column
        self.createEditWindow(path[0])
        return

    def createEditWindow(self, row):
        editwindow = gtk.Window()
        editwindow.set_title("Edit Record %d" % (row + 1))
        #editwindow.set_size_request(400,300)

        table = gtk.Table(len(self.storedFields)+1, 2, False)
        for x in range(0, len(self.storedFields)):
            label = gtk.Label(self.storedFieldLabels[x])
            table.attach(label, 0, 1, x, x+1)

            if (self.storedFields[x] == 'fill'):
                button = gtk.CheckButton(self.storedFieldLabels[x])
                button.set_active(self.recordTable[row][x])
                button.connect("clicked", self.updateBool, row, x)
                table.attach(button, 1, 2, x, x+1)
            else:
                entry = gtk.Entry()
                entry.set_text(self.getText(row,self.storedFields[x]))
                entry.connect("activate", self.updateField, row, x)
                table.attach(entry, 1, 2, x, x+1)

        editwindow.add(table)
        
        editwindow.show_all()
        self.newstatus("Opened window to edit record %d" % (row+1))
        return

    def getColSum(self, field):
        col = self.storedFields.index(field)
        sum = 0
        for i in range(0, len(self.recordTable)):
            sum += float(self.recordTable[i][col])

        return sum

    def getColProdSum(self, field1, field2):
        col1 = self.storedFields.index(field1)
        col2 = self.storedFields.index(field2)
        sum = 0
        for i in range(0, len(self.recordTable)):
            sum += float(self.recordTable[i][col1]) * float(self.recordTable[i][col2])

        return sum

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
        # I think I do want to iterate, so I'll need to modularize the format_...() functions
        # Here's what PHPGMDB was giving me 
        #Number of Records: 	98	records
        #Total Gallons Consumed: 	967 	gallons	
        #Total Miles Travelled: 	28,346 	miles	
        #Total Days on Record: 	1072 (2.93) 	days (years)
        #Total Gas Cost: 	$2,809 	US dollars	
        #Average Gas Mileage: 	29.3 	mpg

        summaryWindow = gtk.Window()
        summaryWindow.set_title("Summary")

        totalGals = self.getColSum('gals')
        totalMiles = self.recordTable[-1][self.storedFields.index('odo')] - self.recordTable[0][self.storedFields.index('odo')]
        totalDays = (self.recordTable[-1][self.storedFields.index('date')] - self.recordTable[0][self.storedFields.index('date')]).days
        totalCost = self.getColProdSum('gals', 'dpg')
        averageMPG = totalMiles / totalGals

        #tableData = { 'Number of Records:': len(self.recordTable), 
        #   'Gallons consumed:': self.getColSum('gals') }
        tableLabels = ['Number of records:', len(self.recordTable), '',
            'Gallons consumed:', "%.1f" % totalGals, 'gal',
            'Miles travelled:', "%d" % totalMiles, 'mi',
            'Days on record:', "%d" % totalDays, 'days',
            'Gas cost:', "%.2f" % totalCost, 'USD',
            'Average miles/gal:', "%.2f" % averageMPG, 'mi/gal',
            ]
        #tableData = [len(self.recordTable), self.getColSum('gals')]

        table = gtk.Table(6, 2, False)
        for i in range(0, len(tableLabels)/3):
            table.attach(gtk.Label(tableLabels[3*i]), 1, 2, i, i+1, ypadding=4, xpadding=8)
            table.attach(gtk.Label(tableLabels[3*i+1]), 2, 3, i, i+1, ypadding=4, xpadding=8)
            table.attach(gtk.Label(tableLabels[3*i+2]), 3, 4, i, i+1, ypadding=4, xpadding=8)

            # Dump to terminal too
            print tableLabels[3*i], "\t", tableLabels[3*i+1], "\t", tableLabels[3*i+2]

        summaryWindow.add(table)

        summaryWindow.show_all()

        self.newstatus("Summary generated.")

        return

    def updateBool(self, button, row, col):
        self.makeDirty()
        self.recordTable[row][col] = button.get_active()
        self.newstatus("Set %s to %s on record %d" % (self.storedFieldLabels[col],"Yes" if button.get_active() else "No",row))
        self.window.queue_draw()
        return

    def updateField(self, entry, row, col):
        self.makeDirty()
        # need to catch exceptions here and throw up errors
        try:
            self.setText(row, self.storedFields[col], entry.get_text())

            # redraw main window here
            self.newstatus("Updated %s on record %d" % (self.storedFieldLabels[col],row))
            self.window.queue_draw()
        except ValueError:
            print 'Caught ValueError'
            #exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            #print "*** print_tb:"
            #traceback.print_tb(exceptionTraceback, limit=1, file=sys.stdout)
            #print "*** print_exception:"
            #traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback,
            #                  limit=2, file=sys.stdout)
            self.show_error('Invalid format, try again.')

        return

    def show_error (self, string):
        md = gtk.MessageDialog(None,
            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
            gtk.BUTTONS_CLOSE, string)
        md.run()
        md.destroy()

    # this function could be parameterized and shared with location and station callbacks
    def format_comment(self, column, cell, model, iter, field):
        row = model.get_value(iter, 0)
        cell.set_property('text', self.getText(row,field))
        return 

    def makeDirty(self):
        self.dirty_bit = True
        self.newstatus("File modified")
        self.setWindowTitle()
        return

    def makeClean(self):
        self.dirty_bit = False
        self.setWindowTitle()
        return

    def setWindowTitle(self):
        if (self.filename == ""):
            self.window.set_title(progname)
        else:
            file_basename = self.filename.split('/')[-1]
	    file_basename = file_basename.split('\\')[-1] # for Winblows compat
            self.window.set_title("%s - %s%s" % (progname, 
                file_basename,
                "*" if self.dirty_bit else ""))
        return

    def on_status_view(self, widget):
        if widget.active: 
            self.statusbar.show()
        else:
            self.statusbar.hide()


PyMPG()
gtk.main()

