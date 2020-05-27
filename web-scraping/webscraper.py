import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
import re
import ssl

#Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

regex1 = re.compile(r"<br/*>", re.IGNORECASE)
regex2 = re.compile(r"</*span>")

def openNextPage(soup):
    tags = soup.find_all(class_="a-last")
    tag = tags[0]
    anchortag = tag.a
    if anchortag is None:
        return
    else:
        next_page_url = anchortag['href']
        next_page_url = 'https://www.amazon.in'+next_page_url
    fhand = urllib.request.urlopen(next_page_url, context = ctx)
    return fhand

review_count = 0
prev_url = ''

review_deposit = open('extract.txt','a',encoding = "utf-8")

url_source = open('url_list_temp.txt','r+')
url = url_source.readline()
while url!='':
    try:
        fhand_1 = urllib.request.urlopen(url.rstrip(), context=ctx)
        html_1 = fhand_1.read()
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        fhand_1.close()

        resume_mode = input('Resume from last blockage? (y/n)')

        if resume_mode=='n':
            #Searching for "See all reviews from India" link
            tags_1 = soup_1.find_all(attrs={"data-hook":"see-all-reviews-link-foot"})
            tag_1 = tags_1[0]
            review_page_url = tag_1['href']
            review_page_url = 'https://www.amazon.in'+review_page_url
            #Opening the reviews page
            fhand = urllib.request.urlopen(review_page_url, context=ctx)

        elif resume_mode=='y':
            fhand = openNextPage(soup_1)

        while fhand is not None:
            html = fhand.read()
            soup = BeautifulSoup(html, 'html.parser')
            tags = soup.find_all('span')
            for tag in tags:
                if len(tag.attrs) > 0:
                    continue
                if tag.i is not None:
                    continue
                elif tag.div is not None:
                    continue
                review_count = review_count + 1
                plain_text = re.sub(regex1,'\n',repr(tag))
                plain_text = re.sub(regex2,'',plain_text)
                review_deposit.write(plain_text+'\n')
                review_deposit.write('-----\n')
                if review_count%100==0:
                    print(review_count)

            prev_url = fhand.geturl()
            fhand.close()
            fhand = openNextPage(soup)

        url = url_source.readline()
    except Exception as e:
        print(e)
        url_source.seek(0,0)
        if prev_url!='':
            url_source.write(prev_url)
            print('Last page url printed in file.')
        break

print('Total number of reviews downloaded:',review_count)
review_deposit.close()
url_source.close()
