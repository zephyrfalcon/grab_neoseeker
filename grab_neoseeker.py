#!/usr/bin/env python3

import getopt
import os
import re
import sys
import urllib.request
from urllib.parse import urlparse
#
from bs4 import BeautifulSoup as BS
import requests


def filename_from_url(url):
    """ Extract the base filename from an URL.
        E.g. "http://faqs.neoseeker.com/Games/DS/foobar.txt" => "foobar.txt"
    """
    url_parts = urlparse(url)
    return os.path.basename(url_parts.path)

# dodgy default cookie. may need to be replaced
DEFAULT_COOKIE = "ns=1t2ilpdrkr49s1tbl9rgp801b5;_gaost=.nv=1.r=www_d_google_d_com.rk=null;_gaos=.gaos_r=www_d_google_d_com.mc=(no)|(no)|(no).gaos_k=null.pc=1;_nrlsk=nrlsk_c=3.et=1466645187; _gat=1;_ga=GA1.2.389298541.1466645409"

class Options:
    debug = False


class NeoSeekerGrabber:

    def __init__(self, faq_url, dirname, options):
        self.faq_url = url
        self.dirname = dirname
        self.options = options
        self.make_target_directory()

    def make_target_directory(self):
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)

    def fetch_url(self, url, origin):
        """ Fetch the contents of the given URL, using HTTP GET and custom
            headers to keep NeoSeeker happy. Return a tuple (content,
            encoding).       
        """
        headers = {
            "Referer": origin, 
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            #"Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8,de;q=0.6,nl;q=0.4",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Cookie": DEFAULT_COOKIE, 
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        }
        #print("Fetching:", url, "with origin:", origin)
        '''
        req = urllib.request.Request(url, headers=headers) 
        u = urllib.request.urlopen(req)
        data = u.read() # assume it's small enough that we can read it all at once
        '''
        r = requests.get(url, headers=headers)
        #print(url, "has encoding:", r.encoding)
        #data = r.content # get binary content; ignore encoding
        return r.text, r.encoding
    
    def grab_faqs(self):
        """ Given an URL to a list of FAQs, download all these FAQs. """
        print("Grabbing:", url, "...")
        faq_source, encoding = self.fetch_url(self.faq_url, self.faq_url)

        if self.options.debug:
            print("#DEBUG: Writing FAQ source file...")
            path = os.path.join(self.dirname, "00_faqs.html")
            with open(path, 'w', encoding=encoding) as f:
                f.write(faq_source)

        urls = self.collect_faqs(faq_source) # BeautifulSoup objects
        for link in urls: 
            self.grab_faq(link, self.faq_url)

        if not urls:
            print("No downloadable FAQs found.")

    def grab_faq(self, link, origin):
        """ Grab a FAQ, given a BeautifulSoup Element object (an <a> link).
            The origin URL needs to be specified as well. """
        print("Grabbing:", link, "...")
        url = link['href']
        data, encoding = self.fetch_url(url, origin)
        print("%d characters; encoding %s (%d raw bytes)" % (
              len(data), encoding, len(bytes(data, encoding))))

        if self.options.debug:
            basename = filename_from_url(url) 
            print("Writing source to file:", basename)
            path = os.path.join(self.dirname, basename)
            with open(path, 'w', encoding=encoding) as f:
                f.write(data)

        filetype, resource = self.determine_file_type(data)
        if filetype == "unknown":
            print("*** Unknown file type; skipping")
            return
        elif filetype == "html":
            resource = url # store the HTML page as-is
            src_data = data
        else:
            src_data, encoding = self.fetch_url(resource, url) # raw data
        basename = filename_from_url(resource)
        out_path = os.path.join(self.dirname, basename)
        #print("Writing:", basename, "...")
        print("Writing: %s (%s)..." % (basename, encoding))
        with open(out_path, 'w', encoding=encoding) as f:
            f.write(src_data)

    def collect_faqs(self, html):
        """ Search for all FAQs in the given HTML (a string) and return
            a list of them. Each FAQ link is represented as a BeautifulSoup
            Element object. 
        """
        soup = BS(html, 'html.parser')
        all_links = []

        # there can be multiple sections of FAQs (e.g. non-English ones); scan
        # them all
        for faq_table in soup.find_all(class_="table-list"):
            links = faq_table.find_all('a')
            links = [link for link in links 
                     if link.has_attr('href') 
                     and "/faqs/" in link['href']
                     and not link['href'].endswith("/faqs/")]
            all_links.extend(links)

        if self.options.debug:
            print("Found these links:")
            for idx, link in enumerate(all_links): 
                print(idx+1, link)
        else:
            print("Found", len(all_links), "FAQs")
        return all_links

    def determine_file_type(self, html):
        """ Given the source HTML of a FAQ, determine the type of the actual
            file being linked to (text, HTML, GIF, PNG, etc); return this type
            as a string, plus the URL to the resource. 
        """
        if "view source" in html:
            soup = BS(html, 'html.parser')
            links = soup.find_all('a')
            links = [link for link in links if "view source" in link.text]
            src_url = links[0]['href']
            return ("text", src_url)

        if "(GIF)" in html:
            soup = BS(html, 'html.parser')
            div = soup.find('div', id='faqtxt')
            img = div.find('img')
            src_url = img['src']
            return ("gif", src_url)

        if "(PNG)" in html:
            soup = BS(html, 'html.parser')
            div = soup.find('div', id='faqtxt')
            img = div.find('img')
            src_url = img['src']
            return ("png", src_url)
        
        if "(PDF)" in html:
            soup = BS(html, 'html.parser')
            div = soup.find('div', id='faqtxt')
            img = div.find('embed')
            src_url = img['src']
            return ("pdf", src_url)

        if "faqtable" in html or b"author_area" in html:
            return ("html", None)

        return ("unknown", "")

def determine_dir_name(url):
    """ Given an URL to a list of FAQs, try to determine a directory name from
        it. This should be the "id" of the game, e.g.
        "http://www.neoseeker.com/pokemon-white/faqs/" => "pokemon-white"
    """
    re_name = re.compile("/(.*?)/faqs")
    url_parts = urlparse(url)
    m = re_name.search(url_parts.path)
    if m is not None:
        return m.group(1)
    else:
        return "unknown"

if __name__ == "__main__":

    opts, args = getopt.getopt(sys.argv[1:], "d")
    url = args[0]
    assert "/faqs" in url, "This does not look like a NeoSeeker FAQs page."
    if args[1:]:
        dirname = args[1]
    else:
        # try to figure out reasonable directory name from URL
        dirname = determine_dir_name(url)
        print("Storing in directory:", dirname)

    options = Options()

    # set options from command line arguments...
    for o, a in opts:
        if o == "-d":
            options.debug = True

    grabber = NeoSeekerGrabber(url, dirname, options)

    grabber.grab_faqs()

