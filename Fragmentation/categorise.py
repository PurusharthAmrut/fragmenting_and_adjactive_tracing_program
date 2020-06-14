import re
import nltk
import json
from csv import reader
from ReviewClass import Noun
from ReviewClass import Fragment

def surround(word):
    return '\\b'+word+'\\b'

# THIS FUNCTION NEEDS TO BE REFINED!
def preprocess(sentence):
    temp1 = re.sub(r'[^\x00-\x7F]',' ',sentence.lower())
    str1 = '"#$%&\'*+-/:;<=>[\\]^_`{|}~()'
    temp2 = re.sub('['+re.escape(str1)+']+',' ',temp1)
    temp3 = re.sub('[.,?!]{2,}',' ',temp2)
    return temp3

def subfragment(review):
    tok_sents = nltk.sent_tokenize(review)
    result = []
    for tok_sent in tok_sents:
        div_sents = tok_sent.split('\n')
        if len(div_sents)==1:
            result.append(div_sents[0])
        else:
            for sent in div_sents:
                result.append(sent)
    return result

def categorise(tok_sents):

    with open('categories.csv','r') as handle:
        csv_reader = reader(handle)
        source_list = list(csv_reader)[0]

    # gonna be a list of fragment objects
    cat_fragments = []
    uncat_sents = []
    matched_categories = dict()
    for sentence in tok_sents:
        parse_sentence = preprocess(sentence)
        match = re.search('|'.join(map(surround,iter(source_list))),parse_sentence)
        pos = 0
        i = 0
        while match is not None:
            # excluding the serializing number from the regex group name
            category = re.sub(r'([a-z_])\d*',r'\1',match.lastgroup,flags=re.A)
            pos = match.start() + pos + 1
            if category not in matched_categories:
                # currently filling without subcategories
                matched_categories[category] = None
            # matching for the next iteration
            match = re.search('|'.join(map(surround,iter(source_list))),parse_sentence[pos+1:])
        if len(matched_categories)==0:
            # collecting the uncategorised sentences to return back
            uncat_sents.append(sentence)
        else:
            cat_fragments.append(Fragment(sentence,parse_sentence,matched_categories.copy()))
            matched_categories.clear()

    return cat_fragments,uncat_sents

def furtherCategorise(tok_sents):
    '''This function looks for independent subcategories in the remaining
    sentences and maps them back to their categories, hence producing
    fragments with categories as well as subcategories'''

    with open('ind_subcats.json','r') as handle:
        ind_component_list = json.load(handle)

    fragments = []
    matched_tree = dict()
    matched_subcategories = dict()
    for sentence in tok_sents:
        parse_sentence = preprocess(sentence)
        for category in ind_component_list:
            match = re.search('|'.join(map(surround,iter(ind_component_list[category]))),parse_sentence)
            pos = 0
            while match is not None:
                # excluding the serializing number from the regex group name
                subcategory = re.sub(r'([a-z_])\d*',r'\1',match.lastgroup,flags=re.A)
                pos = match.start() + pos + 1
                if subcategory not in matched_subcategories:
                    matched_subcategories[subcategory] = match.group()
                # matching for the next iteration
                match = re.search('|'.join(map(surround,iter(ind_component_list[category]))),parse_sentence[pos+1:])
            if len(matched_subcategories)!=0:
                matched_tree[category] = [Noun(word,match) for (word,match) in matched_subcategories.items()]
                matched_subcategories.clear()
        if len(matched_tree)!=0:
            fragments.append(Fragment(sentence,parse_sentence,matched_tree.copy()))
            matched_tree.clear()
        # else: continue

    return fragments

def subcategorise(cat_fragments):

    with open('subcats.json','r') as handle:
        component_list = json.load(handle)

    matched_subcategories = dict()
    for fragment in cat_fragments:
        text = fragment.text_processed
        for category in fragment.categories:
            match = re.search('|'.join(map(surround,iter(component_list[category]))),text)
            pos = 0
            while match is not None:
                # excluding the serializing number from the regex group name
                subcategory = re.sub(r'([a-z_])\d*',r'\1',match.lastgroup,flags=re.A)
                pos = match.start() + pos + 1
                if subcategory not in matched_subcategories:
                    matched_subcategories[subcategory] = match.group()
                # matching for the next iteration
                match = re.search('|'.join(map(surround,iter(component_list[category]))),text[pos+1:])
            if len(matched_subcategories)!=0:
                fragment.categories[category] = [Noun(word,match) for (word,match) in matched_subcategories.items()]
                matched_subcategories.clear()

# fragments must be preprocessed by the above function
# we currently don't have the match for the subcategory words. We will have to store it before doing the extraction of adjectives
def getAdjectives(cat_fragments):
    '''takes a list of fragment objects and gets adjectives of each subcategory
    in the text of the fragment'''

    grammar = r'''NPC: {<VB.?><IN|DT>*<NN.?><[^,\.]*>*<NPB>}
    NPD: {<NN.?><IN><[^,\.]*?>*?<NN.?><VB.?><[^,\.]*?>*?<JJ.?>}
    NPB: {<RB.*>*<JJ.?>+<NN.*>+}
    NPA: {<NN.?>+<[^,\.]*>*?<JJ><NN.?>*}'''
    cp = nltk.RegexpParser(grammar,loop=2)
    # NPC is currently kept for sub-fragmentation
    chunkfilter = lambda e:re.search(r'NP[ABD]',e.label()) is not None

    for fragment in cat_fragments:
        # parsing starts here...
        fragment_tok = nltk.word_tokenize(fragment.text_processed)
        fragment_tag = nltk.pos_tag(fragment_tok)
        tree = cp.parse(fragment_tag)
        # now we will attach adjectives (if available) to each of the category words

        for category in fragment.categories:
            if fragment.categories[category] is None:
                continue
            for subcategory in fragment.categories[category]:
                # a list of adjectives/adverbs associated with the noun in every chunk
                describing_words = []
                # searching for adjectives in every chunk
                for chunk in tree.subtrees(filter = chunkfilter):
                    tagged_words = dict(chunk.leaves())
                    describing_word = []
                    # if this chunk contains descrbing words for the particular
                    # category(noun) in consideration, we collect the describing words
                    if subcategory.match in tagged_words:
                        for word,tag in tagged_words.items():
                            if re.search('RB.?|JJ.?',tag) is not None:
                                describing_word.append(word)
                    else:
                        continue
                    # joining the list of adverbs and adjectives into one string
                    describing_words.append(' '.join(describing_word))
                subcategory.adjectives = describing_words
        # we don't need the clean text anymore
        del fragment.text_processed

with open('test.txt','r',encoding='utf-8') as source:
    review = source.read()

# 1st pass: parsing for category words
cat_fragments,uncat_sents = categorise(subfragment(review))
if len(uncat_sents)!=0:
    # 2nd pass: parsing for subcategory words and ignoring the remaining sentences
    remaining_fragments = furtherCategorise(uncat_sents)
else:
    remaining_fragments = []
# subcategorising the categorised fragments obtained from the 1st pass
subcategorise(cat_fragments)
fragment_list = cat_fragments + remaining_fragments
getAdjectives(fragment_list)

# This part is only for displaying the output
for fragment in fragment_list:
    print(fragment.text)
    categories = fragment.categories
    for category in categories:
        print('Category:',category)
        if categories[category] is None:
            continue
        for subcategory in categories[category]:
            print('\tSubcategory:',subcategory.word)
            print('\tAdjectives:',subcategory.adjectives)
    print('-----------------------------------------------------------------')
