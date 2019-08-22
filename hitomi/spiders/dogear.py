# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import struct
import os
import json

class DogearSpider(scrapy.Spider):
    name = 'dogear'
    num_front = 2
    allowed_domains = ['hitomi.la']
    start_urls = ['https://ltn.hitomi.la/group/dogear-all.nozomi']
    base_path = './data'
    # def start_requests(self):
    #     yield Request("https://ltn.hitomi.la/group/dogear-all.nozomi", dont_filter=True)
    #     pass

    def parse(self, response):
        num = int(len(response.body) / 4)
        books = struct.unpack('>'+'I'*num, response.body)
        # yield response.follow('https://hitomi.la/galleries/{0}.html' % books, meta = {'id': books})
        for b in books:
            # yield response.follow('https://hitomi.la/reader/{}.html'.format(b), self.parse_book, meta = {'id': b})
            yield response.follow('https://ltn.hitomi.la/galleries/{}.js'.format(b), self.parse_book, meta = {'id': b})
        pass

    def parse_book(self, response):
        # https://hitomi.la/reader/1336102.html#1
        # url = response.css("div.img-url::text")[-1].extract()
        # url = url.split("/")[-1]
        # last = url.split(".")[0]
        # if len(last) > 3:
        #     return
        meta = response.meta
        bId = int(meta['id'])

        subId = bId % 10
        if subId == 1:
            subId = 0
        sub = str(chr(subId % self.num_front + 97)) + 'a'
        domain = sub + '.hitomi.la'
        index = response.body.index(b'[')
        data = json.loads(response.body[index:])
        h = {'Referer':'https://hitomi.la/reader/{}.html'.format(bId)}
        for page in data:
            # check dupulicated
            if os.path.exists(os.path.join(self.base_path, str(bId), page['name'])):
                self.logger.info("found dupulicated from {} for id {}".format(page['name'], bId))
                continue
            
            if 'haswebp' in page and page['haswebp'] == 1:
                yield response.follow("https://{}/webp/{}/{}.webp".format(domain, bId, page['name']), self.save_img, headers=h, meta=meta)
            else:
                yield response.follow('https://{}/galleries/{}/{}'.format(domain, bId, page['name']), self.save_img, headers=h, meta=meta)

    def check_path(self, id):
        path = os.path.join(self.base_path, str(id))
        return os.path.exists(path)

    def save_img(self, response):
        filename = response.url.split("/")[-1]
        path = os.path.join(self.base_path, str(response.meta['id']))

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, filename), 'wb') as f:
            f.write(response.body)
        self.logger.info('Save file %s', filename)
        pass
