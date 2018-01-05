import os

import numpy as np
import pandas as pd
import math
import os
import sys
import time
import utm
import requests
from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.data = []

    def handle_starttag(self, tag, attrs):
        # only parse 'anchor' tags
        filenames = []
        if tag == 'a':
            # check the list of defined attributes
            for name, value in attrs:
                # file ending we're looking for:
                target_substring = 'FPVR50_rv12_TA.csv'
                # if href is defined, print it
                # should add a try--except here in order to
                # catch missing files
                # and other ways to catch a lack of forecast data
                if name == 'href' and target_substring in value:
                    self.data.append(value)


def get_html_string(url):
    return requests.get(url).text
