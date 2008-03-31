# Makefile for PGMDB
# Ryan Helinski a.k.a. teh h4x0r3r
#
# This is usually revised before each major update
#
SOURCES := $(shell ls Makefile changelog.txt *.css *.php *.gp)
DIRS = images
EXCLUDE = "*/.svn*"

VERSION := $(shell grep "Version:" changelog.txt | cut -d: -f2 | sed 's/ //')
SVNREV := $(shell svn info | grep "Last Changed Rev: " | cut -d: -f2 | sed 's/ //')

TARBALL = pgmdb-$(VERSION)-r$(SVNREV).tar.bz2
TAROPTS = --create --dereference --verbose --bzip2

# The first rule is the default rule!
install: $(SOURCES)
	chmod -R a+r . 
	mkdir -p var 
	if [ ! -f "var/datafiles.txt" ] ; then echo "" > var/datafiles.txt ; fi
	chmod -R a+rwx var

release:
	make $(TARBALL)
	md5sum $(TARBALL) > $(TARBALL).md5

# This one makes a tarball for mass distribution
$(TARBALL): $(SOURCES) $(DIRS)
	tar $(TAROPTS) --file=$(TARBALL) \
		--exclude=$(EXCLUDE) $(SOURCES) $(DIRS) ;


