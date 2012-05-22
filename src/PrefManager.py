# defaults
# TODO scratch that, they should be loaded independently since they are 
# platform-specific. 
import os
import xml.etree.ElementTree as etree

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

class PrefManager:
	UserPreferences = dict({
		'GnuPlotPath' : 'gnuplot', 
		# might use 'os.name' here
		'GnuPlotTerm' : ''
		}) 

	def __init__(self):
		self.prefFile = os.path.expanduser(os.path.join('~', '.pympg', 'pympg.xml'))

		if (os.path.isfile(self.prefFile)):
			self.load()
		else:
			self.save()

	def load(self):
		mytree = etree.parse(self.prefFile)
		myroot = mytree.getroot()

		for child in myroot[0]:
			if (child.tag == 'pref'):
				print "User Preferences: " + child.attrib['name'] + " = " + pref.attrib['value']
				self.UserPreferences[child.attrib['name']] = pref.attrib['value']

		print "Loaded preferences from '%s'" % self.prefFile

	def save(self):
		myxml = etree.Element('xml', attrib={'version':'1.0', 'encoding':'UTF-8'})
		for pref in self.UserPreferences.keys():
			etree.SubElement(myxml, 'pref', attrib={'name':pref, 'value':self.UserPreferences[pref]})

		if (not os.path.isdir(os.path.dirname(self.prefFile))):
			os.mkdir(os.path.dirname(self.prefFile))
		xmlfile = open(self.prefFile, 'w')
		#xml_indent(myxml) # add white space to XML DOM to result in pretty printed string
		xmlfile.write(etree.tostring(xml_index(myxml)))
		xmlfile.flush()
		xmlfile.close()
	
	def __setitem__(self, key, value):
		self.UserPreferences[key] = value
	
	def __getitem__(self, key):
		return self.UserPreferences[key]

	def __len__(self):
		return len(self.UserPreferences)

	def __contains__(self, field):
		return field in self.UserPreferences

	def keys(self):
		return self.UserPreferences.keys()

	
