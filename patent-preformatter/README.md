# Formatting scripts for patent search results

Here is a collection of R scripts for transforming primary results of patent
search to a common format. Primary results can be gathered from the following
public databases:

 - [Espacenet](https://worldwide.espacenet.com) (use `espacenet.R`)
 - [Google Patents](http://patents.google.com) (use `google.R`)
 - [Patentscope](https://patentscope.wipo.int) (use `patentscope.R`)
 - [Rospatent](https://searchplatform.rospatent.gov.ru) (use `rospatent.R`)

## Prerequisites

Before running, please make sure, that input XLSX/XLS files with search results
have titles as their first rows.

To run scripts, [R environment](https://www.r-project.org) should be installed.
After that, `readxl` and `writexl` packages should be installed too. To perform
this, do the following in R interpreter console:
```R
install.packages("readxl")
install.packages("writexl")
```

## How to run scripts

For the properly formatted XLSX file every script can be executed in the
following way:
```console
Rscript <script-name> <XLSX-file-name>
```
See `run-all.sh` script as example.
