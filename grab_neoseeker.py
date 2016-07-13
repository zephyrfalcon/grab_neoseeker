#!/usr/bin/env python3

import getopt
import os
import re
import sys
import urllib.request
from urllib.parse import urlparse
#
from bs4 import BeautifulSoup as BS

class Options:
    debug = False

def fetch_url(url, origin):
    headers = {
        #"Host": "www.neoseeker.com", 
        "Referer": origin, 
        #"User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #"Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "en-US,en;q=0.8,de;q=0.6,nl;q=0.4",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        # XXX cookie might need to be replaced
        "Cookie": "ns=1t2ilpdrkr49s1tbl9rgp801b5;_gaost=.nv=1.r=www_d_google_d_com.rk=null;_gaos=.gaos_r=www_d_google_d_com.mc=(no)|(no)|(no).gaos_k=null.pc=1;_nrlsk=nrlsk_c=3.et=1466645187; _gat=1;_ga=GA1.2.389298541.1466645409",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    }
    #print("Fetching:", url, "with origin:", origin)
    req = urllib.request.Request(url, headers=headers, origin_req_host=origin)
    u = urllib.request.urlopen(req)
    data = u.read() # assume it's small enough that we can read it all at once
    return data

def filename_from_url(url):
    url_parts = urlparse(url)
    return os.path.basename(url_parts.path)


class NeoSeekerGrabber:

    def __init__(self, url, dirname, options):
        self.url = url
        self.dirname = dirname
        self.options = options
        self.make_target_directory()

    def make_target_directory(self):
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)

    def grab_faqs(self, url):
        print("Grabbing:", url, "...")
        faq_source = fetch_url(url, url)

        if self.options.debug:
            print("#DEBUG: Writing FAQ source file...")
            path = os.path.join(self.dirname, "00_faqs.html")
            with open(path, 'wb') as f:
                f.write(faq_source)

        faq_urls = self.collect_faqs(faq_source) # BeautifulSoup objects
        for link in faq_urls: 
            self.grab_faq(link, url)

    def grab_faq(self, link, origin):
        print("Grabbing:", link, "...")
        url = link['href']
        data = fetch_url(url, origin)
        print(len(data), "bytes")

        if self.options.debug:
            basename = filename_from_url(url) 
            print("Writing source to file:", basename)
            path = os.path.join(self.dirname, basename)
            with open(path, 'wb') as f:
                f.write(data)

        filetype, resource = self.determine_file_type(data)
        if filetype == "unknown":
            print("*** Unknown file type; skipping")
            return
        elif filetype == "html":
            resource = url # store the HTML page as-is
            src_data = data
        else:
            src_data = fetch_url(resource, url) # raw data
        basename = filename_from_url(resource)
        out_path = os.path.join(self.dirname, basename)
        print("Writing:", basename, "...")
        with open(out_path, 'wb') as f:
            f.write(src_data)

    def collect_faqs(self, html):
        soup = BS(html, 'html.parser')
        all_links = []

        # there can be multiple sections of FAQs (e.g. non-English ones); scan
        # them all
        for faq_table in soup.find_all(class_="table-list"):
            links = faq_table.find_all('a')
            print("###", links)
            links = [link for link in links 
                     if link.has_key('href') 
                     and "/faqs/" in link['href']
                     and not link['href'].endswith("/faqs/")]
            all_links.extend(links)

        print("Found these links:")
        for idx, link in enumerate(all_links): print(idx, link)
        return all_links

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
        
        if b"(PDF)" in html:
            soup = BS(html, 'html.parser')
            div = soup.find('div', id='faqtxt')
            img = div.find('embed')
            src_url = img['src']
            return ("pdf", src_url)

        if b"faqtable" in html or b"author_area" in html:
            return ("html", None)

        return ("unknown", "")

def determine_dir_name(url):
    re_name = re.compile("/(.*?)/faqs")
    url_parts = urlparse(url)
    m = re_name.search(url_parts.path)
    if m is not None:
        return m.group(1)
    else:
        return "unknown"

if __name__ == "__main__":

    opts, args = getopt.getopt(sys.argv[1:], "")
    url = args[0]
    assert "/faqs" in url, "This does not look like a NeoSeeker FAQs page."
    if args[1:]:
        dirname = args[1]
    else:
        # try to figure out reasonable directory name from URL
        dirname = determine_dir_name(url)
        print("Storing in directory:", dirname)

    options = Options()
    # TODO: set options from command line arguments...

    grabber = NeoSeekerGrabber(url, dirname, options)

    grabber.grab_faqs(url)

