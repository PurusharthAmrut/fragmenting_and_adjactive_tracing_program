import pandas as pd
import re
import nltk
from tqdm import tqdm
import math

## Replace this function with your own.
def subfragment(review):
    tok_sents = nltk.sent_tokenize(review)
    result = []
    for tok_sent in tok_sents:
        div_sents = re.split(r'[\n.?]',tok_sent)
        if len(div_sents)==1:
            result.append(div_sents[0])
        else:
            for sent in div_sents:
                if sent=='':
                    continue
                result.append(sent)
    return result


dataset_chunks = pd.read_csv("final_dataset.csv", chunksize=1000)
polarity_labelled = pd.DataFrame(columns= ['sentence', 'neg', 'neu', 'pos', 'compound', 'sentiment'])
polarity_labelled_val = pd.DataFrame(columns= ['sentence', 'neg', 'neu', 'pos', 'compound', 'sentiment'])
polarity_labelled.to_csv('amazon_final_vader.csv',mode= 'w')
polarity_labelled_val.to_csv('amazon_final_vader_val.csv',mode= 'w')

## IMPORTANT!! ##

# Replace the total by the total number of reviews to be analysed.
with tqdm(total = 120172) as pbar:
    for chunk in dataset_chunks:
        reviews = chunk['Reviews']
        polarity = []
        tot = len(reviews)
        testing_portion = math.floor(0.8*tot)
        n = 0
        for review in reviews:
            n+=1
            fragment_list = subfragment(review)
            for fragment in fragment_list:
                if len(nltk.word_tokenize(fragment)) < 4:
                    continue
                elif len(nltk.word_tokenize(fragment)) > 200:
                    continue
                fragment = fragment.lower()
                score = analyzer.polarity_scores(fragment)
                neg = score['neg']
                neu = score['neu']
                pos = score['pos']
                compound = score['compound']
                # Default sentiment is neutral. Consider changing it if neccessary.
                sentiment = 2
                if n <= testing_portion:
                    polarity_labelled = polarity_labelled.append({
                        'sentence':fragment,
                        'neg':neg,
                        'neu':neu,
                        'pos':pos,
                        'compound':compound,
                        'sentiment':sentiment},
                        ignore_index = True) 
                else:
                    polarity_labelled_val = polarity_labelled_val.append({
                        'sentence':fragment,
                        'neg':neg,
                        'neu':neu,
                        'pos':pos,
                        'compound':compound,
                        'sentiment':sentiment},
                        ignore_index = True) 
            pbar.update(1)
        
        polarity_labelled.to_csv('amazon_final_vader.csv', mode = 'a', header=False)
        polarity_labelled_val.to_csv('amazon_final_vader_val.csv', mode = 'a', header=False)
        polarity_labelled.drop(polarity_labelled.index, inplace = True)
        polarity_labelled_val.drop(polarity_labelled_val.index, inplace = True)
