import re

fhand1 = open('extract_with_rating.txt','r',encoding='utf-8')
text = fhand1.read()
fhand1.close()
fhand2 = open('cleaned_extract_with_rating.txt','w',encoding='utf-8')
bug = re.compile(r'. 1996-2020, Amazon.com, Inc. or its affiliates\s+\S+\s')
replace = re.sub(bug,'',text)
fhand2.write(replace)
fhand2.close()
