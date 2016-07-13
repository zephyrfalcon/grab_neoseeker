Simple script to grab game FAQs from NeoSeeker.

### Requirements

* Python 3.x (developed and tested on 3.5; other versions may work as
  well)
* [BeautifulSoup 4](https://www.crummy.com/software/BeautifulSoup/bs4/)
  (HTML parsing library)
* [requests](http://docs.python-requests.org/en/master/)

Just run:

```
./grab_neoseeker.py http://www.neoseeker.com/example-game/faqs/
```

The URL must point to a list of FAQs (as opposed to the main page for a
game); such an URL will usually end in `"/faqs/"`. This will download all the FAQs
for the given game (this includes plain text files, HTML files, PDFs,
and images like GIFs and PNGs). It does **NOT** download videos. The
script will automatically create a directory `example-game` to store the
downloaded files in. If you specify another argument, this is taken to
be the directory name instead:

```
./grab_neoseeker.py http://www.neoseeker.com/example-game/faqs/ my-stuff
```

### Notes

This script is strictly meant for personal use. I wrote it so I could
easily get all the FAQs for a game I am playing. It is **NOT** meant to
make offline copies of large numbers of FAQs (doing so will be a lot of
work, and is likely to get you banned by NeoSeeker anyway).

(Some years ago I wrote a similar script for GameFAQs, but this is now
defunct. It was an arms race anyway and eventually GameFAQs removed the
original names of their ASCII FAQs. Not sure if NeoSeeker will go the
same way eventually...)

