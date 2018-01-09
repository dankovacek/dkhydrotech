# EC Climate Data Scraper

A python script to generate a pdf forecast of specific
weather variables for a forecast region.  

### Environment, Dependencies
Python 3.[4, 5, 6].  Python 3.5 is only version verified.

For packages, see requirements.txt.  The only unusual package is utm,
but it can be worked around without too much trouble.  

### Setup
  1.  Clone repo to local system.
  2.  `>>virtualenv -p python3 env`
  3.  If virtualenv not activated: `>>source env/bin/activate` (from main folder)
  4.  `>>pip install requirements.txt`
  5.  `>>python main.py`


### Execution

The example code has a default forecast region for Whistler, BC:

  * FPVR50|rv12|Whistler|Whistler (seems to be 72 hr forecast)

Once you have addressed all of the input parameters in `Setup`:
  * `>>python main.py`


### Setting up realtime retrieval of new data as it is published (AMQP)

Format your command parameters by looking at the folder structure in:
http://dd.weather.gc.ca/


Example config file for SWOB (file named swob.conf)
https://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config/swob.conf

broker amqp://dd.weather.gc.ca/
# All stations
# subtopic observations.swob-ml.#

# Only station CMML (Whistler)
subtopic observations.swob-ml.*.CMML.#
accept .*



### License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2017, Dan Kovacek
