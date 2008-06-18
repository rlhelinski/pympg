# Makefile for documentation

SOURCENAME = pgmdb-user-manual

all:
	make $(SOURCENAME).tex && \
	make $(SOURCENAME).pdf && \
	make $(SOURCENAME) ;

$(SOURCENAME).tex: $(SOURCENAME).lyx
	lyx $(SOURCENAME).lyx --export latex

$(SOURCENAME).pdf: $(SOURCENAME).lyx
	lyx $(SOURCENAME).lyx --export pdf
#	pdfetex $(SOURCENAME).tex 

$(SOURCENAME): $(SOURCENAME).tex
	latex2html -split 0 -no_navigation -show_section_numbers -no_subdir $(SOURCENAME).tex

