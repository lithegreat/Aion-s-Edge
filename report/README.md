# Report Module

This directory is a self-contained LaTeX module for writing reports
related to the course and the experiments in this repository.

## Structure

- `main.tex`: main report file
- `sections/`: report sections split into smaller files
- `references.bib`: bibliography database
- `Makefile`: build and cleanup commands

## Build

```bash
make pdf
```

The generated PDF is written to `build/main.pdf`.

## GitHub Actions

The repository includes a GitHub Actions workflow at
`.github/workflows/report.yml`.

- Any change to the report sources triggers an automatic PDF build.
- On pushes to the `main` branch, the workflow also creates a GitHub
	Release and uploads the generated report PDF.

## Clean

```bash
make clean
```