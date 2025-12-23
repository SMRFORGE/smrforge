@echo off
REM Generate Sphinx API documentation for Windows
REM Run this from the repository root

cd docs

REM Generate API documentation
echo Generating API documentation...
sphinx-apidoc -o api ..\smrforge --separate --module-first

REM Build HTML documentation
echo Building HTML documentation...
sphinx-build -b html . _build\html

echo.
echo Documentation generated in docs\_build\html\
echo Open docs\_build\html\index.html in your browser

