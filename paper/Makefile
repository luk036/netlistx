# Build the IEEEtran two-column paper (Pandoc-Markdown -> PDF).
#
# Reproduce with:  make            (from the paper/ directory)
#
# The build is two-step because pandoc always emits `longtable`, which the
# IEEEtran class forbids in two-column mode:
#   1. pandoc             : Markdown + metadata -> LaTeX (cleveref + IEEE CSL)
#   2. longtable_to_table : rewrite each longtable into a single-column `table`
#                           float and fix column widths to the column text width
#   3. latexmk            : compile to PDF, rerunning for cleveref and citations
#
# Flags and the reason each is present:
#   -F pandoc-crossref          resolve @sec:/@fig:/@tbl:/@lst:/@eq: (cleveref)
#   --citeproc                  IEEE numeric citations from refs.bib + ieee.csl
#   -s -t latex                 standalone LaTeX
#   -N                          number sections
#   --reference-links           link-based (not inline-note) citation style
#   --resource-path=.:figures   find figure files relative to paper/ and figures/
#
# Heading levels: the title lives in YAML metadata, so body headings use "#"
#   for \section; no --shift-heading-level-by is needed.
#
# Offline: the CSL is vendored as ieee.csl, so --citeproc needs no network.

PAPER  := comb_optim
PANDOC := pandoc
FLAGS  := -F pandoc-crossref --citeproc -s -t latex -N --reference-links \
          --resource-path=.:figures
META   := $(PAPER).yaml latex.yaml crossref.yaml

FIGSVG := $(wildcard figures/*.svg)
FIGPDF := $(FIGSVG:.svg=.pdf)

.PHONY: all paper tex figures clean

all: paper

paper: $(PAPER).pdf

tex: $(PAPER).tex

# pdflatex cannot read SVG.  cairosvg converts vectorially and preserves the
# <text> elements (unlike a bare rsvg-convert without fontconfig, which drops
# them).  Do not use ImageMagick -- it rasterises the figures.
figures: $(FIGPDF)

figures/%.pdf: figures/%.svg
	cairosvg $< -o $@

$(PAPER).tex: $(META) $(PAPER).md refs.bib ieee.csl $(FIGPDF)
	$(PANDOC) $(FLAGS) $(META) $(PAPER).md -o $@
	python longtable_to_table.py $@

$(PAPER).pdf: $(PAPER).tex
	latexmk -pdf -interaction=nonstopmode -file-line-error $(PAPER).tex

clean:
	-latexmk -C $(PAPER).tex
	-$(RM) $(PAPER).tex $(FIGPDF)
