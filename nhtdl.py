#!/usr/bin/env python3

import os, sys, argparse, json
from nhentai.parser import doujinshi_parser, search_parser
from nhentai.doujinshi import Doujinshi
from nhentai.downloader import Downloader
from nhentai.utils import generate_cbz
from tqdm import tqdm

argdict = {
    'jp': 'japanese',
    'en': 'english',
    'ch': 'chinese',
}

local_data = os.path.expanduser('~/.nhentai.json')


def init(keyword='', save_dir=''):
    if not os.path.exists(local_data):
        with open(local_data, 'w+') as f:
            f.write("{}")
    with open(local_data, 'r+') as f:
        data = json.load(f)
        if keyword or ('keyword' not in data):
            data['keyword'] = keyword
        if save_dir or ('save_dir' not in data):
            data['save_dir'] = save_dir
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()


def parse_cli():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-l",
            "--language",
            dest='language',
            choices=['jp', 'en', 'ch'],
        )
        parser.add_argument(
            "-c",
            "--category",
            dest='category',
            choices=['doujinshi', 'manga'],
        )
        parser.add_argument(
            "-t",
            "--tags",
            nargs='+',
            dest='tags',
        )
        parser.add_argument(
            "-p",
            "--pages",
            type=int,
            dest='pages',
        )
        parser.set_defaults(language='jp')
        parser.set_defaults(pages=1)
        return parser.parse_args()
    except argparse.ArgumentError as err:
        print(str(err))
        sys.exit(2)


def download(keyword='', pages=1, save_dir=''):
    with open(local_data, 'r+') as f:
        data = json.load(f)
        if not keyword:
            keyword = data['keyword']
        else:
            data['keyword'] = keyword
        if not save_dir:
            save_dir = data['save_dir']
        else:
            data['save_dir'] = save_dir

        downloader = Downloader(path=save_dir, thread=5, timeout=30)
        for page in range(1, pages + 1):
            print('\rIndexing...', end='')
            doujinshi_list = []
            doujinshis = search_parser(keyword, page)
            doujinshi_ids = map(lambda d: d['id'], doujinshis)
            for id_ in doujinshi_ids:
                if str(id_) in data:
                    continue
                doujinshi_info = doujinshi_parser(id_)
                data[str(id_)] = doujinshi_info
                doujinshi_list.append(
                    Doujinshi(name_format='[%i] %s', **doujinshi_info))
            print('Finished.')

            bar = tqdm(
                doujinshi_list,
                bar_format='{l_bar}{bar}{{{n_fmt}/{total_fmt}{postfix}}}',
                dynamic_ncols=True)
            for doujinshi in bar:
                bar.set_description(f'{doujinshi.id}, {doujinshi.pages} pages')
                doujinshi.downloader = downloader
                bar.set_postfix_str('Downloading...')
                doujinshi.download()
                bar.set_postfix_str('Packaging...')
                generate_cbz(save_dir, doujinshi, True)
                bar.set_postfix_str('Finished.')

        for k in data.keys():
            if "ext" in data[k]:
                data[k].pop("ext")

        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()


init()

if len(sys.argv) <= 1:
    download()
else:
    args = parse_cli()
    keyword = [f'Language:{argdict[args.language]}']
    if args.category:
        keyword.append(f'Categories:{args.category}')
    if args.tags:
        for tag in args.tags:
            keyword.append(f"Tags:\"{tag}\"")

    keyword = ' '.join(keyword)
    download(keyword, args.pages)
