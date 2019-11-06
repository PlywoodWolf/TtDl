#!/usr/bin/python
# import multiprocessing as mp
from bs4 import BeautifulSoup as bS
# import requests as rq
from requests.compat import urljoin
import asyncio
import aiohttp
import sys


debug = 1
startUrl = 'https://thetrove.net/Assets/Maps%20&%20Tiles/'


class LinkList:
    def __init__(self):
        dprint('creating LinkList obj')
        self.visited = set()
        self.files = dict()
        dprint('visited = ', self.visited)

    async def filter(self, lst):
        f = [lnk for lnk in lst if lnk not in self.visited]
        return f

    async def add(self, url):
        self.visited.add(url)

    async def addf(self, files):
        dprint('adding', files, 'to files list')
        [self.files.update({file[0]:file[1]}) for file in files]


async def fetch(session, url):
    # dprint('fetching', url)
    async with session.get(url) as response:
        # dprint('fetching', url)
        return await response.text()


def dprint(*line):
    global debug
    if debug:
        print(line, file=sys.stderr)


def parse_links(resp, url):
    soup = bS(resp, 'html.parser')
    links = [urljoin(url, tr.find('a').get('href'))+'/' for tr in soup.find_all('tr', class_='litem dir')]
    dprint(url, links)
    return links


def parse_files(resp, url):
    soup = bS(resp, 'html.parser')
    items = soup.find_all('tr', class_='litem file')
    # dprint(items[0].find('td', class_='litem_size'))
    files = [(urljoin(url, tr.find('a').get('href')), tr.find('td', class_='litem_size').string) for tr in items]
    dprint(url, files)
    return files


async def crawl(name, urls, visited, session):
    while True:
        url = await urls.get()
        dprint(name, 'fetching', url)
        resp = await fetch(session, url)
        await visited.add(url)
        dprint(name, 'adding', url, 'to visited')
        filtered = await visited.filter(parse_links(resp, url))
        files = parse_files(resp, url)
        await visited.addf(files)
        dprint(name, 'filtered url list', filtered)
        [await urls.put(k) for k in filtered]
    # files |= {urljoin(url, td.find('a').get('href')) for td in soup.find_all('tr', class_='litem file')}
        urls.task_done()
        print('Queue length :', urls.qsize())


async def main(url):
    urls = asyncio.Queue()
    visited = LinkList()
    await urls.put(url)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(200):
            task = asyncio.create_task(crawl(f'worker-{i}', urls, visited, session))
            tasks.append(task)

        dprint(urls.qsize())
        await urls.join()

    for task in tasks:
        task.cancel()
    print('Files found :', len(visited.files))
    print('Pages visited :', len(visited.visited))
    defs = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
    size = sum([float(lh) * defs[rh] for lh, rh in [e.split() for e in visited.files.values()]])
    sd = 'GB'
    print('Total file size is {:0.5} {}'.format(size / defs[sd], sd))
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main(startUrl))
