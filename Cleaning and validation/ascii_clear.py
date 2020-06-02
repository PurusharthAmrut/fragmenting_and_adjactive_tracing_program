import re

source = open('dataset.csv','r',encoding='utf-8')
text = source.read()
source.close()
deposit = open('cleaned_dataset.csv','w')
clean_text = re.sub(r'[^\x00-\x7F]','',text)
deposit.write(clean_text)
