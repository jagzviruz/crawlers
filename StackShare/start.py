__author__ = 'jagzviruz'
import requests
import shutil
import re
import time
import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from urllib.request import urlopen

from bs4 import BeautifulSoup
from pymongo import MongoClient

start = time.time()

class StackShare:
    def __init__(self):
        self.homePage = 'http://stackshare.io'
        self.startUrl = '/categories'
        self.make_sure_path_exists("images")

    def make_sure_path_exists(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def notify_me_after_crawling_done(self):
        me = "crawler@jagzlabs.com"
        you = "k.jagdish@gmail.com"

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Hurrah !! Crawled"
        msg['From'] = me
        msg['To'] = you

        # Create the body of the message (a plain-text and an HTML version).
        text = "Hi! The crawling is done."
        html = """\
        <html>
          <head></head>
          <body>
            <p>Hi!<br>
               The craling is <b>done</b>.
            </p>
          </body>
        </html>
        """

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        # Send the message via local SMTP server.
        s = smtplib.SMTP('localhost')
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail(me, you, msg.as_string())
        s.quit()

    def fetch_all_categories_URLs_from_start_page(self):
        page = urlopen(self.homePage + self.startUrl).read()
        bsPageObj = BeautifulSoup(page, "html5lib")
        services = bsPageObj.find_all('div', class_="stacked-service")
        categories = []

        for tmp in services:
            parentCategory = tmp.find('div', class_="categories-stack-name").find('span').get_text()
            sub_cats = tmp.find_all('span', itemprop='applicationSubCategory')

            for sub_cat in sub_cats:
                t_dict = {}
                t_dict['name'] = sub_cat.get_text()
                t_dict['url'] = sub_cat.find('a')['href']
                t_dict['parentCategory'] = parentCategory
                categories.append(t_dict)

        return categories

    def download_technology_image(self,technology_name, image_url):
        ext = image_url.split(".")[-1]
        technology_name = technology_name.replace("#","sharp")
        technology_name = re.sub('[^0-9a-zA-Z]+', '', technology_name)
        technology_name = technology_name.lower()
        image_name = "images/" + technology_name + "." + ext

        f = open(image_name,'wb')
        f.write(requests.get(image_url).content)
        f.close()
        return image_name


    def fetch_all_technologies_in_category(self, category):

        category_name = category['name']
        url = self.homePage + category['url']
        page = urlopen(url).read()
        bs_page_obj =BeautifulSoup(page, "html5lib")
        stacks = bs_page_obj.find_all('div', class_="stacked-service")
        technologies = []

        for stack in stacks:
            tmp = {}
            tech_name = stack.find('div', class_='landing-stack-name').find('a').get_text()

            prev_record = db.technologies.find_one({
                "technology_name": tech_name
            })

            if prev_record:
                print(prev_record)

            else:
                tmp['technology_name'] = tech_name
                tmp['technology_image_url'] = stack.find('div', class_='service-logo').find('a').find('img')['src']

                if tmp['technology_image_url'] and 'no-img-open-source.png' not in tmp['technology_image_url']:
                    tmp['downloaded_image'] = self.download_technology_image(tech_name, tmp['technology_image_url'])
                else:
                    tmp['downloaded_image'] = "/images/na.png"

                tmp['technology_url'] = stack.find('div', class_='service-logo').find('a')['href']
                tmp['technology_category'] = [category_name]


            print("Got all data for : " + tech_name)
            technologies.append(tmp)
            print("Time elapsed : " + str(time.time() - start))
            time.sleep(1)
            print("Sleep over . Time elapsed : " + str(time.time() - start))

        return technologies

print("Started at : " + str(start))
client = MongoClient()
client.drop_database('tools_and_technologies')
db = client.tools_and_technologies

if os.path.exists("images"):
    shutil.rmtree('images')

test = StackShare()
categories = test.fetch_all_categories_URLs_from_start_page()

if len(categories) > 0:
    print("Got " + str(len(categories)) + " categories")
    db.categories.insert(categories)

    for category in categories:
        print("Checking out %s", category)

        technologies = test.fetch_all_technologies_in_category(category)
        if len(technologies) > 0:
            print("Got " + str(len(technologies)) + " technologies in " + category['name'])
            db.technologies.insert(technologies)
        else:
            print("No Technologies for " + category['name'])


test.notify_me_after_crawling_done()