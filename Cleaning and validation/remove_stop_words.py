import re

def surround(word):
    return '\\b'+re.escape(word)+'\\b'

def multiple_replace(stop_words, text):
    # Create a regular expression  from the dictionary keys
    regex = re.compile('|'.join(map(surround, iter(stop_words))),flags=re.I)
    #regex = re.compile('\\bhello\\b|\\bhey\\b', flags=re.I)

    # For each match, look-up corresponding value in dictionary
    return regex.sub('', text).strip()

list = ['hello','hey']
print(multiple_replace(list, ' hello I am hellololololo'))
