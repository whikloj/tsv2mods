# tsv2mods.py

This script is used to generate multiple [MODS](http://www.loc.gov/standards/mods/) records from a tab-deliminated file.

This script is fairly simple and is not useful for very complex data structures.

## Usage

```
usage: tsv2mods.py [-h] [-o OUTPUT_DIR] [-e]
                   [-d {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-w]
                   files

Turn a Tab Seperated Value file of MODS data into a bunch of MODS files.

positional arguments:
  files                 A TSV file to process

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        Directory to output files to, defaults to current
                        working directory.
  -e, --include-empty-tags
                        Include empty XML elements in the output document.
                        Defaults to skip them.
  -d {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --debug {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set logging level, defaults to ERROR.
  -w, --overwrite       Overwrite existing files with the same name, defaults
                        to skipping
```
### Logging
By default a log file called `tsv2mods.log` is generated in the current directory you run the script in. You can change the logging level
by using one of the options with the `-d` or `--debug` argument.

## Input data format

The first column of the file will be used to generate the output filenames, by taking the data and appending '.mods'

The files first row is expected to have the XPath statements to the elements to put the data into.

The remaining rows contain the data values.

So the contents of the first column and first row is actually discarded.

Elements that have no corresponding value or omitted by default. You can alter this with the `-e | --include-empty-tags` switch.

### Examples

A spreadsheet like
```
Filename ➡ /mods:typeOfResource ➡ /mods:name/mods:namePart ➡ /mods:name/mods:role/mods:roleTerm@type=code ➡ /mods:name/mods:role/mods:roleTerm@type=text ➡ /mods:titleInfo/mods:title ➡ /mods:originInfo/mods:dateCreated
AAA ➡ still image ➡ Smith, Bob ➡ cre ➡ ➡ A photo ➡ 2018
BBB ➡ moving image ➡ Young, Jane ➡ ➡ Dancer ➡ Swan Lake ➡ 2017
```
Would create 2 files 

_Note_: The actual output files have no line breaks or indenting to save space, those are added below for readability.

AAA.mods
```
<?xml version='1.0' encoding='UTF-8'?>
<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
    <mods:typeOfResource>still image</mods:typeOfResource>
    <mods:name>
        <mods:namePart>Smith, Bob</mods:namePart>
        <mods:role>
            <mods:roleTerm type="code">cre</mods:roleTerm>
        </mods:role>
    </mods:name>
    <mods:titleInfo>
        <mods:title>A photo</mods:title>
    </mods:titleInfo>
    <mods:originInfo>
        <mods:dateCreated>2018</mods:dateCreated>
    </mods:originInfo>
</mods:mods>
```
and
BBB.mods
```
<?xml version='1.0' encoding='UTF-8'?>
<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
    <mods:typeOfResource>moving image</mods:typeOfResource>
    <mods:name>
        <mods:namePart>Young, Jane</mods:namePart>
        <mods:role>
            <mods:roleTerm type="text">Dancer</mods:roleTerm>
        </mods:role>
    </mods:name>
    <mods:titleInfo>
        <mods:title>Swan Lake</mods:title>
    </mods:titleInfo>
    <mods:originInfo>
        <mods:dateCreated>2017</mods:dateCreated>
    </mods:originInfo>
</mods:mods>
```
 
## License
MIT
