# kibanchizu-converter

## Summary
"Kiban Chizu Jouho(基盤地図情報)" is one of the Japanese GIS dataset provided by The Geospatial Information Authority of Japan (GSI). The dataset is needed to be converted to adequate file formats because it is encoded by comforming to ISO 19100 series. The converting tool is provided by GSI, but the tool is only for Windows users. Because of this reason, I developed a simple tool for Linux users who need convert tool for "Kiban Chizu Jouho(基盤地図情報)". This tool is developed by Python 2.7 scripts, and the GUI interface is designed by PyQt5. This tool can be work on both Linux and Mac though I haven't tested on Mac. 

## Requirements
This tool uses following Python modules: sys, os, zipfile, sys, time, PyQt5, codecs, chardet and ElementTree. Please install these Python modules before using. 

## How to run
The simplest way to run is open the terminal and type "run.sh", or type like "python main.py". The interface is very simple. 

1. Select the input directory, which stores XML files of "Kiban Chizu Jouho(基盤地図情報)". 
2. Select the output directory for saving outcomes.
3. Press the button of "Convert!!".
4. Wait a while.
5. Open GIS software and import the converted data.

Note that XML files should be unziped. In the case you downloaded "Kiban Chizu Jouho(基盤地図情報)" by bulk downloading mode, the downloaded data should have named like as "PackDLMap.zip". Therefore you need to extract all files contained in the "PackDLMap" directories before using this this tool.
Each resultant is written as colon separating text file. Geometry columns of basic items are encoded as WKT types and DEM items are encoded as simple Lat/Lon columns. These data are easily imported to QGIS.

## Important!!
This tool is under developing, and it may have essential problems. So, please check results carefully before you publish any maps by using this tool, and the author recomend that you DON'T use the current version at any official works.
