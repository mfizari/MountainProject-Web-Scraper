import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
from collections import defaultdict


class UserSpider(CrawlSpider):
    name = 'users'
    allowed_domains = ['mountainproject.com']
    start_urls = [
        'https://www.mountainproject.com']  # start here in the area tree



    #Look for user pages only in area pages, route pages, and route stat pages
    #This should exclude route/num/?print=1 and route/num/add/photo, all forum pages, etc.
    regex_search = [
        'https://www.mountainproject.com/area/[0-9]+/([a-z0-9\-]+)(?:(?!.))', #go to any area page
        "https://www\.mountainproject\.com/route/[0-9]+/([a-z0-9\-]+)(?:(?!.))", #go to any route page
        "https://www\.mountainproject\.com/route/stats/[0-9]+/([a-z0-9\-]+)(?:(?!.))" #go to any route's stat page
    ]

    #Look for user home pages with this regex
    regex_user = "https://www\.mountainproject\.com/user/[0-9]+/([a-z0-9\-]+)(?:(?!.))"  # call parse_user from here!
    #Deny everything on the user's page except the tick page
    regex_user_deny = [
        'https://www\.mountainproject\.com/user/[0-9]+/([a-z0-9\-]+)/contributions',
        'https://www\.mountainproject\.com/user/[0-9]+/([a-z0-9\-]+)/community',
        'https://www\.mountainproject\.com/user/[0-9]+/([a-z0-9\-]+)/tick-export',
        'https://www\.mountainproject\.com/user/[0-9]+/([a-z0-9\-]+)/todo-export',
        'https://www\.mountainproject\.com/user/[0-9]+/([a-z0-9\-]+)/climb-todo-list'
    ]


    rules = (
        Rule(LinkExtractor(allow=regex_search)),
        Rule(LinkExtractor(allow=regex_user, deny=regex_user_deny), callback='parse_userpage')
    )

    # This is the method for getting the user's name, location, age, gender, and signup date
    def ExtractUserDemo(self, response):
        name = str(response.css('div.col-xs-12.text-xs-center h2::text').getall()[0])  # string

        location = [x for x in [x.strip() for x in
                                response.xpath("//div[@class='col-xs-12 text-xs-center']/div[@class='']/text()").
                                    extract()] if x != '']  # list
        if not location:
            location = ''  # empty string if no location listed

        userdemo = str(
            [x.strip() for x in response.xpath("//div[@class='col-xs-12 text-xs-center']/div[@class='']//div/text()")
                .extract()])

        age = str([x for x in [z.strip() for z in userdemo.split('d\\n')] if any(y in x for y in ['year'])])
        age = re.findall(r'\d+', age)  # list
        if age:
            age = int(age[0])  # int
        else:
            age = 0

        gender = str(
            [x.strip() for x in [z.strip() for z in userdemo.split('d\\n')] if any(y in x for y in ['ale', 'ying'])])
        if 'Male' in gender:
            gender = 'Male'
        elif 'Female' in gender:
            gender = 'Female'
        elif 'ying' in gender:
            gender = 'NotSaying'
        if not gender:
            gender = ''

        signupdate = str(response.xpath("//div[@class='info mt-1']/div[2]/text()").extract()[0])
        if not signupdate:
            signupdate = ''

        userinfo = {
            'Name': name,
            'Location': location,
            'Age': age,
            'Gender': gender,
            'SignupDate': signupdate
        }
        return userinfo

    # This is the method for getting all tick data from a single page
    def ExtractTickDataPage(self, response):
        rowspath = "//table[@class='table route-table hidden-xs-down']/tr[@class!='screen-reader-only']"
        rowdata = response.xpath(rowspath)  # 2 rows for each climb
        date = []  # list with 1 element: string
        name = []  # list with 1 element: string
        rating = []  # list with more than one element (append)
        routetype = []  # list > 1 str el
        location = []  # list > 1 str el
        style = []  # list with one el.
        pitches = []  # list with 1 el
        note = []  # list with one el.
        url = []  # list with one el.
        for i, row in enumerate(rowdata):  # Even rows have name etc, odd rows have

            if i % 2 == 0:  # even row: contains name,rating,routettype,location,pitches
                iname = row.xpath("td[1]/a/strong/text()").extract()
                iurl = row.xpath("td[1]/a//@href").extract()
                ilocation = row.xpath("td[2]/span[@class='small']/span[@class='text-warm']/a/text()").extract()
                irating = row.xpath("td[4]/span[@class='rateYDS']/text()").extract()  # YDS rating only (blank if none)
                itype = row.xpath("td[4]/span[@class='small text-warm pl-half']/span/text()").extract()
                ipitches = row.xpath(
                    "td[4]/span[@class='small text-warm pl-half']/span[@class='text-nowrap']/text()").extract()

                if len(iname) > 0:  # list is populated
                    iname = str(iname[0])
                else:
                    iname = ''
                name.append(iname)  # list with 1 element: string
                rating.append(irating)  # list with more than one element (append)
                routetype.append(itype)
                location.append(ilocation)  # list > 1 str el
                pitches.append(ipitches)  # list with 1 el
                url.append(iurl)  # list with one el.
            else:
                itext = row.xpath("td[1]/i/text()").extract()  # assume this can be empty
                if not itext:  # somehow no text was found
                    idate = []  # always output as a list
                    istyle = []  # always output as a list
                    inote = []  # always output as a list
                else:
                    itext = itext[0].split(' · ')
                    idate = itext[0].strip()  # this is a string
                    if len(itext) == 1:  # there was only a date
                        istyle = []
                        inote = []
                    else:
                        text = itext[1].strip()
                        if bool(re.match(r"^\d+ pitches\.", text)):  # empty if no pitches in string
                            text = text.replace(str(re.findall(r"^\d+ pitches\.", text)[0]), '').strip()
                        text_split = text.split('.')  # spit on 1st period. Could be empty if pitches only
                        styles = ['Solo', 'Lead / Redpoint', 'Lead / Fell/Hung', 'Lead', 'Lead / Flash',
                                  'Lead / Onsight',
                                  'TR', 'Send', 'Flash', 'Attempt', 'Lead / Pinkpoint', 'Follow']
                        if text_split[0] != '':  # contained more than pitch count
                            if text_split[0].strip() in styles:  # style found
                                istyle = [text_split[0].strip()]
                                if len(text_split) > 1:  # and note
                                    inote = [text_split[1]]
                                else:  # no note
                                    inote = []
                            else:  # Style not found - only note
                                inote = [text]
                                istyle = []
                        else:
                            istyle = []
                            inote = []

                date.append(idate)
                style.append(list(istyle))
                note.append(list(inote))


        tickdata = {
            'Date': date,  # This is a list of strings
            'Name': name,
            'Rating': rating,
            'RouteType': routetype,
            'Location': location,
            'Style': style,
            'Pitches': pitches,
            'Notes': note,
            'URL': url,  # and here!
        }


        return tickdata

    # Parse the user page and try to go to their tick page - don't output data if ticks are private
    def parse_userpage(self, response):
        # Extract user info and put into item
        userinfo = self.ExtractUserDemo(response)
        item = {'UserInfo': userinfo, 'Date': [], 'Name': [], 'Rating': [], 'RouteType': [], 'Location': [],
                'Style': [], 'Pitches': [], 'Notes': [], 'URL': []}
        meta = {'item': item}  # meta allows you to pass this item into your next parse method
        #
        # Get tick page url if ticks are not private
        tickurl = [link for link in response.xpath("//span[@class='font-body pl-1']/a/@href").extract()
                   if 'ticks' in link]

        # Open tick page to start scraping!
        if tickurl:  # if tick link is found
            tickurl = str(tickurl[0])  # convert to string so you can follow this link
            yield scrapy.Request(tickurl, callback=self.parse_opentickpage, meta=meta)

    # This gets all the
    def parse_opentickpage(self, response):
        item = response.meta['item']  # pass item with userinfo into this method.
        meta = {'item': item}  # guess I have to do this again? Up here since I'm not adding anything to item

        # Get a list of all tickpage links: urls for every page of the user ticks (including page 1)
        lastpagelink = [link for link in response.xpath("//div[@class='pagination']/a/@href").extract()]
        firstpagelink = response.url
        if lastpagelink:
            npages = int(lastpagelink[1].split('=')[1])  # number of pages
            allpagelinks = [firstpagelink] + [firstpagelink + '?page=' + str(i) for i in range(2, npages + 1)]
        else:
            npages = 1
            allpagelinks = [firstpagelink]

        # Scrape first page of ticks, since CrawlSpider doesn't visit any pages twice ...
        # Get page data and add to item values (all lists?)
        page_tickdata = self.ExtractTickDataPage(response)
        # Need to convert each list of lists into real values
        item['Date'].extend(page_tickdata['Date'])
        item['Name'].extend(page_tickdata['Name'])
        item['Rating'].extend(page_tickdata['Rating'])
        item['RouteType'].extend(page_tickdata['RouteType'])
        item['Location'].extend(page_tickdata['Location'])
        item['Style'].extend(page_tickdata['Style'])
        item['Pitches'].extend(page_tickdata['Pitches'])
        item['Notes'].extend(page_tickdata['Notes'])
        item['URL'].extend(page_tickdata['URL'])

        if npages > 1:  # recursively keep parsing pages
            start_tickurl = allpagelinks[1]  # start recursive parsing on the second page
            pagecounter = 2  # start count at second page
            yield scrapy.Request(start_tickurl,
                                 callback=lambda url: self.parse_ticks(url, npages, pagecounter),
                                 meta=meta)

        else:  # output item if it's the only page
            yield item

    def parse_ticks(self, response, npages, pagecounter):
        # This method calls in item, parses info from tick page and updates item. Then adds one to tick page
        # and calls itself if there are more pages to get

        # First import item and append
        item = response.meta['item']  # get item from meta so you can append to it
        # Get page data and add to item values
        page_tickdata = self.ExtractTickDataPage(response)
        item['Date'].extend(page_tickdata['Date'])
        item['Name'].extend(page_tickdata['Name'])
        item['Rating'].extend(page_tickdata['Rating'])
        item['RouteType'].extend(page_tickdata['RouteType'])
        item['Location'].extend(page_tickdata['Location'])
        item['Style'].extend(page_tickdata['Style'])
        item['Pitches'].extend(page_tickdata['Pitches'])
        item['Notes'].extend(page_tickdata['Notes'])
        item['URL'].extend(page_tickdata['URL'])

        # item['Testing'].append('1') #Add to the testing list if this page is visited

        # Update meta, which will be passed into method in callback automatically?
        meta = {'item': item}

        # Update pagecounter
        pagecounter = pagecounter + 1  # will exceed npages on the last call
        tickurl = response.url

        if pagecounter <= npages:  # up to and including the last page
            tickurl = tickurl.split('=')[0] + '=' + str(pagecounter)  # generate url to follow for the next page
            yield scrapy.Request(tickurl,
                                 callback=lambda url: self.parse_ticks(url, npages, pagecounter),
                                 meta=meta)
        else:  # you're on the lastpage+1, yield item
            yield item
