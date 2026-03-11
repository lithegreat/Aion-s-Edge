TARGET := main
OUTDIR := build
LATEXMK := latexmk

.PHONY: pdf clean

pdf:
	mkdir -p $(OUTDIR)
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error \
		-outdir=$(OUTDIR) $(TARGET).tex

clean:
	$(LATEXMK) -C -outdir=$(OUTDIR)
	rm -rf $(OUTDIR)