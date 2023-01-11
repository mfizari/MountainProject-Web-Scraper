# MountainProject-Web-Scraper
This repository contains code that can be used with Scrapy, the web-scraping python framework, to scrape information on routes and users on Mountainproject.com <br/>

### Installation
First, it is strongly recommended to operate Scrapy in a virtual environment. In Windows, use:
```
py -m venv directory
```

Navigate to the venv directory in git bash, then clone this repository:
```
$ git clone https://github.com/mfizari/MountainProject-Web-Scraper
```

Install scrapy in your venv:
```
pip install scrapy
```


### Running the scraper
The spiders in the `/spiders` are CrawlSpiders that will crawl along links following defined rules. <br/>
The CrawlSpider in `scrpRoutes` is restricted to crawling along area pages and route pages. When it gets to a route page, it calls `parse_routepage`, which extracts the relevant data from the route page into an item, including the name, rating, number of votes, FA information, and list of ticks, star ratings, and rating suggestions from users. **Note**: As of the initial commit for this project, MountainProject returns an error when trying to load the stats pages for routes with >1000 votes. This is handled with the `errback` method in `parse_routepage`. <br/>
The CrawlSpider in `scrpUsers` is restricted to crawling along area, route, route stat, and user pages. When it gets to a user page, the parse method checks if the user has public ticks, then crawls through every page of the ticks and extracts all the information into an item, including the demographic information on the user's homepage. <br/>

To run either of the CrawlSpiders, navigate to the root directory of the project and run the command:<br/>
```
scrapy crawl scrpNAME -o FILENAME.jl
```
Where NAME indicates Routes or Users This will save the item in a JSON lines file in the project directory. 
