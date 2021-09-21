from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from autocorrect import Speller
import re
import string

# The purpose of this pre-processor is to tokenize the text meaningfully
# to aid the process of Text-Embedding for the AI engine.

# 1: Noise like extra whitespaces (trailing and consecutive), newline, etc.
# are removed which may otherwise interfere with the tokenization.
# We will also convert all the letters to lowercase.
# We will use the regex patterning in python for this purpose.

def text_cleaner(text):
    rules = [
        {r'>\s+': u'>'},  # remove spaces after a tag opens or closes
        {r'\s+': u' '},  # replace consecutive spaces
        {r'\s*<br\s*/?>\s*': u'\n'},  # newline after a <br>
        {r'</(div)\s*>\s*': u'\n'},  # newline after </p> and </div> and <h1/>...
        {r'</(p|h\d)\s*>\s*': u'\n\n'},  # newline after </p> and </div> and <h1/>...
        {r'<head>.*<\s*(/head|body)[^>]*>': u''},  # remove <head> to </head>
        {r'<a\s+href="([^"]+)"[^>]*>.*</a>': r'\1'},  # show links instead of texts
        {r'[ \t]*<[^<]*?/?>': u''},  # remove remaining tags
        {r'^\s+': u''}  # remove spaces at the beginning
    ]
    for rule in rules:
        for (k, v) in rule.items():
            regex = re.compile(k)
            text = regex.sub(v, text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text) # remove punctuations
    text = text.rstrip()
    text = text.lower()
    return text

# Now we will break the word into tokens, but to improve the performance
# of the embedder, removal of insignificant words is required.
# Words like is, a, the, are, etc, which are insignificant (called stopwords) 
# for sentiment analysis as well as tagging should be removed to improve
# performance.

def filter_stop_words(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    text_filtered = [x for x in word_tokens if not x in stop_words]
    return text_filtered

# Now we will perfrom stemming and lemmatization.

def stem_and_lemmatize(text_tokenized):
    ps = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    for i in range(0,len(text_tokenized)):
        text_tokenized[i] = ps.stem(text_tokenized[i])
        text_tokenized[i] = lemmatizer.lemmatize(text_tokenized[i])
    return text_tokenized

# Finally, getting everything together.

def text_tokenizer(text):
    text = text_cleaner(text)
    text_tokenized = filter_stop_words(text)
    # Before stemming and lemmatizing, it is important to check and correct
    # any spelling mistakes.
    spell = Speller(lang='en')
    for i in range(0, len(text_tokenized)):
        text_tokenized[i] = spell(text_tokenized[i])
    text_tokenized = stem_and_lemmatize(text_tokenized)
    return text_tokenized

def text_tokenizer_without_stem(text):
    text = text_cleaner(text)
    text_tokenized = filter_stop_words(text)
    # Before stemming and lemmatizing, it is important to check and correct
    # any spelling mistakes.
    spell = Speller(lang='en')
    for i in range(0, len(text_tokenized)):
        text_tokenized[i] = spell(text_tokenized[i])
    return text_tokenized