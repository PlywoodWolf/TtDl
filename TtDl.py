#!/usr/bin/python
# import multiprocessing as mp
from bs4 import BeautifulSoup as bS
import requests as rq
from requests.compat import urljoin
import asyncio
# import aiohttp
import sys


debug = True
visited = {}
files = {}
startUrl = 'https://thetrove.net/index.html'

class linkList:
    def __init__(self):
        dprint('creating linkList obj')
        self.visited = {}
        dprint('visited = ', self.visited)

    def filter(self, lst):
        return [lnk for lnk in lst if lnk not in self.visited]

    def add(self, url):
        dprint('adding', url, 'to visited')
        self.visited.add(url)
        dprint('added', url, 'to visited')



def dprint(*line):
    global debug
    if debug:
        print(line, file=sys.stderr)


def parse_links(resp, url):
    soup = bS(resp.text, 'html.parser')
    return [urljoin(url, td.find('a').get('href')) for td in soup.find_all('tr', class_='litem dir')]
    # [await urls.put(nurl) for nurl in new_urls if nurl not in visited]

async def crawl(name, urls, visited):
    global files
    url = await urls.get()
    resp = rq.get(url)
    dprint(resp.headers)
    visited.add(url)
    dprint('!')
    [await urls.add(k) for k in visited.filter(parse_links(resp, url))]
    dprint(name)
    # files |= {urljoin(url, td.find('a').get('href')) for td in soup.find_all('tr', class_='litem file')}
    dprint(urls.qsize())
    #urls.task_done()


async def main(url):
    # m = mp.Manager()
    # urls = m.Queue()
    # visited = m.Queue()
    # files = m.Queue()
    urls = asyncio.Queue()
    visited = linkList()
    await urls.put(url)

    tasks = []
    for i in range(10):
        task = asyncio.create_task(crawl(f'worker-{i}', urls, visited))
        tasks.append(task)

    await urls.join()

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    # pool = mp.Pool(mp.cpu_count())
    # while not urls.empty():
    #    a = pool.apply_async(crawl, (urls, visited, files), callback=dprint)
    # pool.close()
    # pool.join()

if __name__ == '__main__':
    asyncio.run(main(startUrl))
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main(startUrl))

# crawl(startUrl)
