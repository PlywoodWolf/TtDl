#!/usr/bin/python3.7
import sys
import urllib
import re

parse_re = re.compile('href="([^"]*)".*(..-...-.... ..:..).*?(\d+[^\s<]*|-)')
          # look for          a link    +  a timestamp  + a size ('-' for dir)
def list_apache_dir(url):
#    try:
    html = urllib.urlopen(url).read()
#    except IOError, e:
#        print 'error fetching %s: %s' % (url, e)
#        return
    if not url.endswith('/'):
        url += '/'
    files = parse_re.findall(html)
    dirs = []
    print(url + ' :')
    print('%4d file' % len(files) + 's' * (len(files) != 1))
    for name, date, size in files:
        if size.strip() == '-':
            size = 'dir'
        if name.endswith('/'):
            dirs += [name]
        print('%5s  %s  %s' % (size, date, name))

    for dir in dirs:
        print
        list_apache_dir(url + dir)

for url in sys.argv[1:]:
    print
    list_apache_dir(url)
