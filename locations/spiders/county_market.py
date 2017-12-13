# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


SIEVE = ('View on Map', 'Make My Preferred Store!')
DAYS = r'M|Tue|Wed|Thu|Sat|Sun|Fri|'


class MyCountyMarketSpider(scrapy.Spider):
    name = "county_market"
    allowed_domains = ["www.mycountymarket.com", ]

    start_urls = (
        'http://www.mycountymarket.com/shop/store-locator/',
    )

    def parse_hours(self, hours):
        if re.search(r'24 Hours', hours):
            return '24/7'
        elif not re.search(DAYS, hours.replace(' ', '')):
            return 'Mo-Su {}'.format(re.sub(r'am|pm', ':00', hours.replace(' ', '')))
        else:
            return ''

    def process_store(self, store):

        opening_hours, phone = ('','')
        try:
            data = store.xpath(
                '//div[@class="col-lg-4"]/div/*[not(self::h2 or self::strong)]//text()').extract()
            normalize_data = [val for val in [info.strip()
                                              for info in data] if val]
            final_data = [clean for clean in normalize_data if clean not in SIEVE]
            city, state_zip = final_data[2].split(',')
            state, pcode = state_zip.strip().split()

            if 'Phone Number' in final_data:
                phone = final_data[final_data.index('Phone Number')+1]
            if 'Store Hours' in final_data:
                opening_hours = self.parse_hours(final_data[final_data.index('Store Hours')+1:][0])

        except Exception as e:
            raise e

        props = {
            'addr_full': final_data[1],
            'ref': store.url,
            'city': city,
            'postcode': pcode,
            'state': state,
            'website': store.url,
            'opening_hours': opening_hours,
            'phone': phone,

        }

        yield GeojsonPointItem(**props)

    def parse(self, response):

        stores = response.xpath(
            '//div[@style="padding:5px;"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(url=response.urljoin(store), callback=self.process_store)
