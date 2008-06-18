
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
	latex2html $(SOURCENAME).tex

