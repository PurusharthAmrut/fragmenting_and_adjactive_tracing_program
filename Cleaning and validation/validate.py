import re

fhand = open('extract_with_rating.txt','r',encoding='utf-8')
text = fhand.read()
counter = 1
pos = text.find('\n-----\n')
while pos > 0:
    counter = counter + 1
    if counter%3==0:
        if text[pos+11:pos+17]!='out of':
            print(text[pos+7:pos+40]+'\t'+str(counter))
            break
    text = text[pos+1:]
    pos = text.find('\n-----\n')
fhand.close()