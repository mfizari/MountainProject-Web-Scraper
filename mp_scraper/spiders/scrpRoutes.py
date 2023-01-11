import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re

### Everything here should work and be good to go


class RouteSpider(CrawlSpider):
    name = 'routes'
    allowed_domains = ['mountainproject.com']
    start_urls = ['https://www.mountainproject.com/']  # start here in the area tree

    # Allowed pages - area, route, and route/stats
    regex_area = "https://www\.mountainproject\.com/area/[0-9]+/([a-z0-9\-]+)(?:(?!.))"  # area regex for all areas
    regex_route = "https://www\.mountainproject\.com/route/[0-9]+/([a-z0-9\-]+)(?:(?!.))"  # route regex for all routes

    start_urls = ['https://www.mountainproject.com/area/106905115/fairbanks-and-vicinity']
    regex_area = "https://www\.mountainproject\.com/area/[0-9]+/([a-z0-9\-]+)(?:(?!.))"
    regex_deny_area = "https://www.mountainproject.com/area/105909311/alaska"
    # regex_route = "https://www.mountainproject.com/route/[0-9]+/([a-z0-9\-]+)(?:(?!.))"


    rules = (
        Rule(LinkExtractor(allow=regex_area, deny=regex_deny_area)),  #Go to area pages
        Rule(LinkExtractor(allow=regex_route), callback='parse_routepage') #Go to route pages and get info
    )

    # Defining a bunch of methods to get our data

    # Get the name of the route
    def ExtractName(self, response):
        name = response.css('h1::text').get().strip()
        return name

    # Get the route type info, including type, length, grade, pitches
    def ExtractRouteTypeTable(self, response):
        tablecontents = response.css('table.description-details td::text').getall()
        typestring = [x.strip() for x in tablecontents[1].strip().split(',')]  # List of all strings in table
        keywords = [['Sport', 'Trad', 'Aid', 'TR', 'Boulder', 'Snow', 'Ice', 'Mixed', 'Alpine'], 'ft', 'Grade','pitches']

        # Extract route type and remove from input
        routetype = [val for val in typestring if val in keywords[0]]
        routetype = str(routetype).replace('[', '').replace(']', '').replace('\'', '')
        if routetype:  # if routetype is non-empty
            typestring = [val for i, val in enumerate(typestring) if
                          val not in keywords[0]]  # remaining typestring will be empty if only type is populated

        # Extract route length and remove it from input
        routelength = [val for val in typestring if keywords[1] in val]  # empty if no length elementy
        if routelength:
            routelength = int(str(routelength[0]).split(' ')[0])  # if not empty, output integer as routelength
        else:
            routelength = None
        if routelength:  # if routetype is non-empty
            typestring = [val for i, val in enumerate(typestring) if
                          keywords[1] not in val]  # will be empty if x has type only

        # Extract route grade and remove from input
        routegrade = [val for val in typestring if keywords[2] in val]  # empty if no length elementy
        if routegrade:
            routegrade = str(routegrade[0]).split(' ')[1]  # if not empty, output integer
        else:
            routegrade = None
        if routegrade:  # if routetype is non-empty
            typestring = [val for i, val in enumerate(typestring) if
                          keywords[2] not in val]  # will be empty if x has type only

        # Extract route pitches and remove from input
        routepitches = [val for val in typestring if keywords[3] in val]  # empty if no length elementy
        if routepitches:
            routepitches = int(str(routepitches[0]).split(' ')[0])  # if not empty, output integer
        else:
            routepitches = None

        FAinfo = tablecontents[3].strip()  # string containing all the FA info.

        subdate = response.xpath("//table[@class='description-details']/tr[4]/td[2]/text()").extract()
        if subdate:
            subdate = subdate[1].strip().replace('on ', '')
        else:
            subdate = None


        TypeInfo = {
            'Type': routetype,
            'Length': routelength,
            'Grade': routegrade,
            'Pitches': routepitches,
            'FA': FAinfo,
            'Subdate': subdate
        }

        return TypeInfo

    # Extract route vote information
    def ExtractVoteInfo(self, response):
        votestr = str(
            [x for x in [x.strip() for x in response.css('span::text').getall()] if 'Avg' in x and 'votes' in x])
        voteavg = [float(x) for x in re.findall(r'-?\d+\.?\d*', votestr)][0]
        votecount = int([float(x) for x in re.findall(r'-?\d+\.?\d*', votestr)][1])
        voteinfo = [voteavg, votecount]
        return voteinfo

    # Extract route difficulty rating information
    def ExtractRatingInfo(self, response):
        ratingYDS = [x.strip() for x in response.css('h2.inline-block.mr-2 span.rateYDS::text').getall()]  # list of YDS ratings, empty for non rock climbs
        #ratingYDS is a list of rock grades: both YDS and V, or either individually
        if len(ratingYDS) > 1: #rating was found, it must be both YDS and Vscale
            ratingVscale = ratingYDS[1]
            ratingYDS = ratingYDS[0]
        elif len(ratingYDS) == 1: #route is either pure YDS or pure boulder
            if 'V' in ratingYDS[0]:
                ratingYDS = ratingYDS[0]
                ratingVscale = None
            else:
                ratingYDS = ratingYDS[0]
                ratingVscale = None
        else:
            ratingYDS = None
            ratingVscale = None

        ratingMisc = response.css('h2.inline-block.mr-2::text').getall()  # list of everything in the rating tag
        # remove empites, leaves a string of all other ratings (PG, A3, etc..)
        ratingMisc = [x.strip() for x in ratingMisc if x.strip() != '']
        if not ratingMisc:
            ratingMisc = None
        else: #combine into one string
            ratingMisc = str(ratingMisc).replace('[', '').replace(']', '').replace('\'', '')
            ratingMisc = ratingMisc.replace(' ', ', ')

        ratingInfo = [ratingYDS, ratingVscale, ratingMisc]
        return ratingInfo

    # Extract number of comments!
    def ExtractCommentCount(self, response):
        # Find comment count, returns [] if tag not found
        CommentCount = [x.split(' ')[0] for x in response.css('h2.comment-count::text').getall() if x is not None]
        if CommentCount:
            CommentCount = int(CommentCount[0])  # convert to integer
        else:
            CommentCount = 0  # set equal to zero if tag not found
        return CommentCount

    # Extract the route location
    def ExtractRouteLocation(self, response):
        #Extract location and remove all weird characters with a regex
        Location = [re.sub(r"[^a-zA-Z0-9 ]", "", x) for
                    x in response.css('div.mb-half.small.text-warm a::text').getall()[1::]]

        return Location

    # Extract table information from "Opinions" page
    def ExtractRouteTableInfo(self, response):

        def getstarsfrompage(table):  # input is the table under the div with h3 containing 'Star'
            rowdata = table.css('tr')
            usernames = []
            stars = []
            for i, row in enumerate(rowdata):  # for every row in the table
                usernames += ([x.strip() for x in row.css('td')[0].css('::text').getall() if '\n' not in x])
                stars.append(len([x for x in row.css('td')[1].css('img::attr(src)').getall() if 'star' in x]))
            table_stars = list(
                zip(usernames, stars))  # returns a list of tuples, where each tuple contains username,stars
            return table_stars

        def getratingsfrompage(table):  # input is table in div tag with 'Rating' in h3
            rowdata = table.css('tr')
            usernames = []
            ratings = []
            for i, row in enumerate(rowdata):  # for every row in the table
                usernames += ([x.strip() for x in row.css('td')[0].css('::text').getall() if '\n' not in x])
                ratings += (([x.strip() for x in row.css('td')[1].css('::text').getall()]))
            table_ratings = list(
                zip(usernames, ratings))  # returns a list of tuples, where each tuple contains username,ratings
            return table_ratings

        def getticksfrompage(table):  # input is table in div tag with 'Rating' in h3
            rowdata = table.css('tr')  # every tick row
            usernames = []
            ticks = []

            for i, row in enumerate(rowdata):  # for every row in the table
                usernames += ([x.strip() for x in row.css('td')[0].css('::text').getall() if '\n' not in x])
                rowtext = [x.strip() for x in row.css('td')[1].css('::text').getall()]
                ticks += [x.strip() for x in rowtext if x != '']  # gets multiple ticks just fine!
            table_ticks = list(
                zip(usernames, ticks))  # returns a list of tuples, where each tuple contains username,ratings
            return table_ticks

        keys = ["Stars", "Ratings", "Ticks"]
        tabledict = dict.fromkeys(keys)
        tablenames = [x.strip() for x in response.css('h3::text').getall() if 'Please' not in x]
        tables = response.css('table.table.table-striped')
        # gets all the tables, should be the same length as tablenames!
        if isinstance(tablenames, str):
            tablenames = [tablenames]
        for i, name in enumerate(tablenames):
            if 'Star' in name:
                tabledict['Stars'] = getstarsfrompage(tables[i])
            if 'Rating' in name:
                tabledict['Ratings'] = getratingsfrompage(tables[i])
            if 'Ticks' in name:
                tabledict['Ticks'] = getticksfrompage(tables[i])

        return tabledict


    #Parsing methods ...
    def parse_routepage(self, response):
        ratingInfo = self.ExtractRatingInfo(response)
        TypeInfo = self.ExtractRouteTypeTable(response)
        Location = self.ExtractRouteLocation(response)
        voteinfo = self.ExtractVoteInfo(response)


        keys = ['Name', 'RatingYDS', 'RatingVscale', 'RatingMisc', 'Type','Stars','Votes', 'Location', 'Grade', 'Pitches',
                'Length', 'FA', 'CommentCount', 'GPS', 'DateAdded', 'URL', 'StatsInfo']
        item = dict.fromkeys(keys)
        item['Name'] = self.ExtractName(response)
        item['RatingYDS'] = ratingInfo[0]
        item['RatingVscale'] = ratingInfo[1]
        item['RatingMisc'] = ratingInfo[2]
        item['Type'] = TypeInfo['Type']
        item['Stars'] = voteinfo[0]
        item['Votes'] = voteinfo[1]
        item['Location'] = Location
        item['Grade'] = TypeInfo['Grade']
        item['Pitches'] = TypeInfo['Pitches']
        item['Length'] = TypeInfo['Length']
        item['DateAdded'] = TypeInfo['Subdate']
        item['FA'] = TypeInfo['FA']
        item['CommentCount'] = self.ExtractCommentCount(response)
        item['URL'] = response.url

        # Get the URL for the stats page from the route page and go to it!
        statpage = response.url[0:response.url.find('/route/')+7]+ \
                   'stats/'+response.url[response.url.find('/route/')+7::]

        #Get the URL for the location page that the route is directly under --- CHECK THAT THIS WORKS!!!
        locpage = response.xpath("//div[@class='col-md-9 float-md-right mb-1']"
                                 "/div[@class='mb-half small text-warm']/a[last()]/@href").extract()
        if locpage:
            locpage = str(locpage[0]) #convert to string

        meta = {'item': item} #this is required for passing item between different requests
        yield scrapy.Request(statpage, callback=lambda url: self.parse_statpage(url, locpage),
                             meta=meta,
                             errback=lambda err: self.error_handler(err, meta, locpage)) #error handler for stat page

    def parse_statpage(self, response, locpage):
        item = response.meta['item']  # retrieve the item ...
        item['StatsInfo'] = self.ExtractRouteTableInfo(response)
        meta = {'item': item}
        yield scrapy.Request(locpage, callback= lambda page: self.parse_locpage(page, meta),
                             meta=meta, dont_filter=True,
                             errback=lambda err: self.error_handler2(err, meta))  #error handler for loc page

        # yield item

    def error_handler(self, failure, meta, locpage):
        item = meta['item']
        item['StatsInfo'] = None
        meta = {'item': item}

        yield scrapy.Request(locpage, callback=lambda url: self.parse_locpage(url, meta),
                             meta=meta, dont_filter=True,
                             errback=lambda err: self.error_handler2(err, meta))  # error handler for loc page

    def parse_locpage(self, response,meta):
        item = meta['item']  # retrieve the item ...
        #GPS is either first or second row in table on the route page
        GPS = response.xpath("//table[@class='description-details']//tr[2]/td[2]/text()").extract()
        GPS_marker = response.xpath("//table[@class='description-details']//tr[2]/td[1]/text()").extract()
        if GPS_marker: #is not empty
            if 'GPS' not in GPS_marker[0]: #GPS is first row for whatever raisin
                GPS = response.xpath("//table[@class='description-details']//tr[1]/td[2]/text()").extract()
        if GPS:
            GPS = GPS[0].strip()
        item['GPS'] = GPS
        yield item

    def error_handler2(self, failure, meta):
        item = meta['item']
        yield item


