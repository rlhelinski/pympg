# defaults
# TODO scratch that, they should be loaded independently since they are 
# platform-specific. 
import os
import xml.etree.ElementTree as etree

class PrefManager:
	UserPreferences = dict({
		'GnuPlotPath' : 'gnuplot', 
		# might use 'os.name' here
		'GnuPlotTerm' : ''
		}) 

	def __init__(self):
		self.prefFile = os.path.expanduser('~/.pympg/pympg.xml')

		if (os.path.isfile(self.prefFile)):
			self.load()
		else:
			self.save()

	def load(self):
		mytree = etree.parse(self.prefFile)
		myroot = mytree.getroot()

		for child in myroot[0]:
			if (child.tag == 'pref'):
				self.UserPreferences[child.attrib['name']] = pref.attrib['value']

	def save(self):
		myxml = etree.Element('xml', attrib={'version':'1.0', 'encoding':'UTF-8'})
		for pref in self.UserPreferences.keys():
			etree.SubElement(myxml, 'pref', attrib={'name':pref, 'value':self.UserPreferences[pref]})

		if (not os.path.isdir(os.path.dirname(self.prefFile))):
			os.mkdir(os.path.dirname(self.prefFile))
		xmlfile = open(self.prefFile, 'w')
		#xml_indent(myxml) # add white space to XML DOM to result in pretty printed string
		xmlfile.write(etree.tostring(myxml))
		xmlfile.flush()
		xmlfile.close()
	
