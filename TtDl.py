#!/usr/bin/python3.7
from bs4 import BeautifulSoup as bS
from requests.compat import urljoin
import asyncio
import aiohttp
import sys
import progressbar
import ast
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


debug = 1
startUrl = 'https://thetrove.net/index.html'
bar = progressbar.ProgressBar().start()


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
        return await (response.text('utf-8'), str(response.url) if str(response.url) else url)


def dprint(*line):
    global debug
    if debug:
        print(line, file=sys.stderr)


def parse_links(resp, url):
    soup = bS(resp, 'html.parser')
    links = [urljoin(url, tr.find('a').get('href'))+'/' for tr in soup.find_all('tr', class_='litem dir')]
    dprint(url, links[1:])
    return links[1:]


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
        resp, url = await fetch(session, url)

        await visited.add(url)
        dprint(name, 'adding', url, 'to visited')
        filtered = await visited.filter(parse_links(resp, url))
        files = parse_files(resp, url)
        await visited.addf(files)
        dprint(name, 'filtered url list', filtered)
        [await urls.put(k) for k in filtered]
    # files |= {urljoin(url, td.find('a').get('href')) for td in soup.find_all('tr', class_='litem file')}
        urls.task_done()
        bar.update((len(visited.visited) / (urls.qsize() + len(visited.visited))) * 100)
        print('Queue length :', urls.qsize())


async def main(url):
    app     = QApplication (sys.argv)
    tree    = QTreeWidget ()
    headerItem  = QTreeWidgetItem()
    item    = QTreeWidgetItem()

    urls = asyncio.Queue()
    visited = LinkList()
    try:
        with open("visited.txt", 'r') as f:
            visited.visited = ast.literal_eval(f.read())
            #print(visited.visited)
        with open("files.txt", 'r') as f:
            visited.files = ast.literal_eval(f.read())
            #print(visited.files)
    except:
        pass
    if url not in visited.visited:
        await urls.put(url)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(20):
            task = asyncio.create_task(crawl(f'worker-{i}', urls, visited, session))
            tasks.append(task)

        dprint(urls.qsize())
        await urls.join()

    for task in tasks:
        task.cancel()
    bar.finish()
    print('Files found :', len(visited.files))
    print('Pages visited :', len(visited.visited))
    defs = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
    size = sum([float(lh) * defs[rh] for lh, rh in [e.split() for e in visited.files.values()]])
    sd = 'GB'
    print('Total file size is {:0.5} {}'.format(size / defs[sd], sd))
    await asyncio.gather(*tasks, return_exceptions=True)

    # with open("visited.txt", 'w') as f:
    #    f.write(repr(visited.visited))
    # with open("files.txt", 'w') as f:
    #    f.write(repr(visited.files))

    for i in range(3):
        parent = QTreeWidgetItem(tree)
        parent.setText(0, "Parent {}".format(i))
        parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        for x in range(5):
            child = QTreeWidgetItem(parent)
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            child.setText(0, "Child {}".format(x))
            child.setCheckState(0, Qt.Unchecked)
    tree.show()
    sys.exit(app.exec_())

    while 1:
        dic = visited.files
        cmd = input('Введите команду')
        if cmd == 'q':
            break
        elif cmd == 'r':
            new_base = input('Введите имя каталога')
            ext = input('Введите расширение')
            dic = {k : v for k,v in visited.files.items() if new_base in k if k.split('.')[-1] == ext}
        size = sum([float(lh) * defs[rh] for lh, rh in [e.split() for e in dic.values()]])
        print('Files found :', len(dic))
        print('Total file size is {:0.5} {}'.format(size / defs[sd], sd))
        cmd = input('Вывести ссылки? [y/n]: ')
        if cmd == 'y':
            with open("links.txt", 'a') as f:
                f.write(visited.files)

if __name__ == '__main__':
    asyncio.run(main(startUrl))
