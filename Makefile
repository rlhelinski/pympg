# Makefile for PGMDB
# Ryan Helinski a.k.a. teh h4x0r3r
#
# This should be revised before each major update
#
SOURCES := $(shell ls Makefile CHANGELOG LICENSE INSTALL README *.css *.php)
DOCS := $(shell ls docs/*.html docs/*.pdf)
DIRS = images 
EXCLUDE = "*/.svn*"

VERSION := $(shell cat VERSION )
SVNREV := $(shell svn info | grep "Last Changed Rev: " | cut -d: -f2 | sed 's/ //')

TARBALL = pgmdb-$(VERSION)-r$(SVNREV).tar.bz2
CHECKSUM = pgmdb-$(VERSION)-r$(SVNREV).md5
TAROPTS = --create --dereference --verbose --bzip2

# The first rule is the default rule!
install: $(SOURCES)
	chmod -R a+r . 
	mkdir -p var 
	chmod -R a+rwx var

release:
	make docs
	make $(TARBALL)
	make $(CHECKSUM) 

$(CHECKSUM): $(TARBALL)
	md5sum $(TARBALL) > $(CHECKSUM)

# This one makes a tarball for mass distribution
$(TARBALL): $(SOURCES) $(DIRS)
	tar $(TAROPTS) --file=$(TARBALL) \
		--exclude=$(EXCLUDE) $(DIRS) $(DOCS) $(SOURCES) ;

docs : 
	cd docs; make  

