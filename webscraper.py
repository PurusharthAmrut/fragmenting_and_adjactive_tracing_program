import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
from langdetect import detect
import re
import ssl

#Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


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

regex1 = re.compile(r"<br/*>", re.IGNORECASE)
regex2 = re.compile(r"</*span>")

review_count = 0
prev_url = ''
language_barrier = False

review_deposit = open('extract_with_rating.txt','a',encoding = "utf-8")
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
            fhand.close()
            soup = BeautifulSoup(html, 'html.parser')
            tags = soup.find_all('span', attrs={"data-hook":"review-body"})

            for tag in tags:
                review_count = review_count + 1
                plain_text = re.sub(regex1,'\n',repr(tag.contents[1]))
                plain_text = re.sub(regex2,'',plain_text)
                review_deposit.write(plain_text+'\n')
                review_deposit.write('-----\n')

                #Extracting the star rating for the review
                sibling = tag.parent.parent.find_all(class_="a-row",recursive=False)
                if len(sibling)==0:
                    continue
                review_deposit.write(sibling[1].a['title']+'\n')
                review_deposit.write('-----\n')

                if review_count%100==0:
                    print(review_count)

            prev_url = fhand.geturl()
            fhand = openNextPage(soup)

    except Exception as e:
        print(e)
        url_source.seek(0, 0)
        if prev_url != '':
            url_source.write(prev_url)
            print('Last page url printed in file.')
        break

print('Total number of reviews downloaded:',review_count)
review_deposit.close()
url_source.close()
