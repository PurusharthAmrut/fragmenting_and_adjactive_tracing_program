from csv import reader
import pandas as pd
import re

data = pd.read_csv('final_dataset2.csv')

with open('stop_words.csv','r') as handle:
    csv_reader = reader(handle)
    swords = list(csv_reader)[0]

def surround(word):
    return '\\b'+re.escape(word)+'\\b\s*'

regex = re.compile('|'.join(map(surround, iter(swords))))

print('Processing...')
index = -1
for review in data['Reviews']:
    index = index+1
    data.loc[index,'Reviews'] = re.sub(regex,'',review)
print('...column cleared of stop words')

data.to_csv('final_dataset3.csv',index=False)
print('data stored in final_dataset3.csv')
