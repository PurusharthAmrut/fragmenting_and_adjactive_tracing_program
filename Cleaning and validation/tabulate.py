import re

fhand = open('test.txt','r',encoding='utf-8')
text = fhand.read()
table = dict()
reviews = re.split('\n-----\n',text)

for i in range(0,len(reviews)-2,2):
    table[reviews[i]] = reviews[i+1]
print(table)
fhand.close()
