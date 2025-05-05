# img2pdfbook
Image files to single PDF converter

## usage
```
usage: img2pdfbook.py [-h] [-o FILE] [-d DIR] [--nogui] [-r] [-s SUFFIX] [-i INITCOUNT] [-t DIR] [-m MARGIN] [--split]
                      [--splitmargin SPLITMARGIN] [--splitpage SPLITPAGE] [--leave_temp] [--debug]
                      [img_folder]

convert Image files to single PDF

positional arguments:
  img_folder            folder of input images

options:
  -h, --help            show this help message and exit
  -o, --output_pdf FILE
                        output file name
  -d, --output_dir DIR  output directory
  --nogui               start with CUI
  -r, --recursive       recursive mode
  -s, --suffix SUFFIX   suffix of output file name with recursive mode
  -i, --initcount INITCOUNT
                        initial count in suffix
  -t, --tmpdir DIR      temporary directory
  -m, --margin MARGIN   crop margin at left/right side in pixel
  --split               split image to 2 pages
  --splitmargin SPLITMARGIN
                        crop margin at center for image to be split in pixel
  --splitpage SPLITPAGE
                        pages to be split
  --leave_temp          leave temp files
  --debug               debug mode
  ```
