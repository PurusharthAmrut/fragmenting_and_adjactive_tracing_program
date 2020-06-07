import re
import nltk
import string
from csv import reader

def surround(word):
    return '\\b'+re.escape(word)+'\\b'

with open('categories.csv','r') as handle:
    csv_reader = reader(handle)
    categories = list(csv_reader)[0]

# list containing the category tags
match_list = []

review = "Best camera, very good battery life, eat body material, average weight, best performance, best display and battery."
for sentence in nltk.sent_tokenize(review):
    pos2 = 0
    # finding the first category match
    match1 = re.search('|'.join(map(surround,iter(categories))),sentence,flags=re.I)
    while match1 is not None:
        # offsetting pos1 so that punctuations is found after category word
        pos1 = match1.start()+pos2
        # adding a new category tag
        if repr(match1) not in match_list:
            match_list.append(repr(match1))
        # searching for punctuation to fragment the sentence
        match2 = re.search(r'[.,!?]',sentence[pos1:])
        if match2 is None:
            pos2 = len(sentence)
        else:
            # cancelling the fragmented string's offset so that pos2 is with
            # respect to base of the original string
            pos2 = match2.start()+pos1
        # printing the fragment
        print(sentence[pos1:pos2])
        match1 = re.search('|'.join(map(surround,iter(categories))),sentence[pos2:],flags=re.I)
