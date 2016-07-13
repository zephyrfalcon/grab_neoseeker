#!/usr/bin/env python3

import getopt
import os
import sys
import urllib.request
from urllib.parse import urlparse
#
from bs4 import BeautifulSoup as BS

def fetch_url(url):
    u = urllib.request.urlopen(url)
    data = u.read() # assume it's small enough that we can read it all at once
    return data

def filename_from_url(url):
    url_parts = urlparse(url)
    return os.path.basename(url_parts.path)


class NeoSeekerGrabber:

    def __init__(self, url, dirname):
        self.url = url
        self.dirname = dirname
        self.options = {}
        self.make_target_directory()

    def make_target_directory(self):
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)

    def grab_faqs(self, url):
        print("Grabbing:", url, "...")
        faq_source = fetch_url(url)
        # DEBUG
        path = os.path.join(self.dirname, "00_faqs.html")
        with open(path, 'wb') as f:
            f.write(faq_source)

        faq_urls = self.collect_faqs(faq_source) # BeautifulSoup objects
        for link in faq_urls: 
            self.grab_faq(link)

    def grab_faq(self, link):
        print("Grabbing:", link, "...")
        url = link['href']
        data = fetch_url(url)
        print(len(data), "bytes")

        # DEBUG: write source to file
        basename = filename_from_url(url) 
        path = os.path.join(self.dirname, basename)
        with open(path, 'wb') as f:
            f.write(data)

        filetype, resource = self.determine_file_type(data)
        if filetype == "unknown":
            print("Unknown file type; skipping")
            return
            # TODO: maybe if it's unknown, the FAQ is in HTML, so we need to
            # store that...? 

        src_data = fetch_url(resource) # raw data
        basename = filename_from_url(resource)
        out_path = os.path.join(self.dirname, basename)
        print("Writing:", basename, "...")
        with open(out_path, 'wb') as f:
            f.write(src_data)

    def collect_faqs(self, html):
        soup = BS(html, 'html.parser')
        faq_table = soup.find(class_="table-list")
        links = faq_table.find_all('a')
        links = [link for link in links 
                 if "/faqs/" in link['href'] 
                 and not link['href'].endswith("/faqs/")]
        print("Found these links:")
        for idx, link in enumerate(links): print(idx, link)
        return links

    def determine_file_type(self, html):
        """ Given the source HTML of a FAQ, determine the type of the actual
            file being linked to (text, HTML, GIF, PNG, etc); return this type
            as a string, plus the URL to the resource. 
        """
        if b"view source" in html:
            soup = BS(html, 'html.parser')
            links = soup.find_all('a')
            links = [link for link in links if "view source" in link.text]
            src_url = links[0]['href']
            return ("text", src_url)

        if b"(GIF)" in html:
            soup = BS(html, 'html.parser')
            div = soup.find('div', id='faqtxt')
            img = div.find('img')
            src_url = img['src']
            return ("gif", src_url)

        if b"(PNG)" in html:
            soup = BS(html, 'html.parser')
            div = soup.find('div', id='faqtxt')
            img = div.find('img')
            src_url = img['src']
            return ("png", src_url)

        return ("unknown", "")


if __name__ == "__main__":

    opts, args = getopt.getopt(sys.argv[1:], "")
    url = args[0]
    assert "/faqs" in url, "This does not look like a NeoSeeker FAQs page."
    if args[1:]:
        dirname = args[1]
    else:
        dirname = "target"
        # TODO: try to figure out reasonable directory name from URL

    grabber = NeoSeekerGrabber(url, dirname)

    grabber.grab_faqs(url)

