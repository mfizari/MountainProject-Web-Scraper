# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RouteItem(scrapy.Item):
    pass
    # # define the fields for your item here like:
    # # name = scrapy.Field()
    # Name = scrapy.Field()        #name of climb [str]
    # TypeInfo = scrapy.Field()    #dictionary: {'Type':[list],'Length':[int/none],'Grade':[str/none],'Pitches':[int/none]}
    # FA = scrapy.Field()          #FA info [str]
    # VoteInfo = scrapy.Field()    #Vote information [voteavg, votecount] [list]
    # RatingInfo = scrapy.Field()  #Rating dictionary: {'ratingYDS':[list],'ratingMisc': [list]}
    # CommentInfo = scrapy.Field() #Number of comments [int]