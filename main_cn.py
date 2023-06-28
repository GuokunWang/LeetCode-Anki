from database_cn import create_tables
from crawler_cn import LeetCodeCrawler
from renderer_cn import render_anki

# create database
create_tables()

# start crawler
worker = LeetCodeCrawler()
worker.login()
#worker.fetch_accepted_problems()
worker.fetch_hot100_problems()

# render anki
render_anki()