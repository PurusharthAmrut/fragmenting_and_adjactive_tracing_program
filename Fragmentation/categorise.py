import re
import nltk
import string
from csv import reader

def surround(word):
    return '\\b'+word+'\\b'
def preprocess(sentence):
    sentence = sentence.lower()
    clean_text = re.sub(r'[^\x00-\x7F]|..+|[\'\":;]',' ',sentence)
    return clean_text

with open('categories.csv','r') as handle:
    csv_reader = reader(handle)
    categories = list(csv_reader)[0]

# list containing the category tags
match_list = []
# list containing meaningful fragments
fragments = []
cat_sents = dict()

review = "But when I use the camera on this device, I see flickering of the screen and it is extremely evident even in the video playback. This is ridiculous when you are marketing this device with one of the USP being a great camera."
print(review)

for sentence in nltk.sent_tokenize(review):
    sentence = preprocess(sentence)
    pos2 = 0
    # finding the first category match
    match1 = re.search('|'.join(map(surround,iter(categories))),sentence,flags=re.I)
    while match1 is not None:
        # offsetting pos1 so that the category word is found after the punctuation mark
        pos1 = match1.start()+pos2
        # the string will be fragmented between previous punctuation and next punctuation
        prev_pos2 = pos2
        # searching for next punctuation to fragment the sentence
        match2 = re.search(r'[.,!?]',sentence[pos1:])
        if match2 is None:
            pos2 = len(sentence)
        else:
            # cancelling the fragmented string's offset so that pos2 is with
            # respect to base of the original string
            pos2 = match2.start()+pos1
        # adding a new category tag
        word = match1.group()
        if word not in match_list:
            match_list.append(word)        

        fragments.append(sentence[prev_pos2:pos2])
        match1 = re.search('|'.join(map(surround,iter(categories))),sentence[pos2:],flags=re.I)

print(match_list)
print(fragments)
