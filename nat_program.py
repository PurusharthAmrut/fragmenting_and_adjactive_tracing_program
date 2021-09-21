import re
import os
import nltk
import json
from csv import reader
from googletrans import Translator
from spellchecker import SpellChecker
from ReviewClass import Category,Subcategory,Fragment

dir_path = os.path.abspath(os.path.dirname(__file__)) + '\\'

def ignoreWordsSetup(spellchecker):
    '''Loads words that are to be ignored into the spell checker.
    A csv file of such words is maintained in the ignore_words.csv file'''
    list_path = os.path.join(dir_path,'ignore_words.csv')
    with open(list_path,'r') as handle:
        csv_reader = reader(handle)
        ignore_words = list(csv_reader)[0]

    spellchecker.word_frequency.load_words(ignore_words)
    spellchecker.known(ignore_words)

spell = SpellChecker()
ignoreWordsSetup(spell)

translator = Translator()

def surround(word):
    return '\\b'+word+'\\b'

# THIS FUNCTION CAN BE REFINED
def preprocess(sentence):
    # eliminating all non-ASCII characters and lower-casing the sentence
    temp1 = re.sub(r'[^\x00-\x7F]',' ',sentence.strip().lower())
    temp2 = re.sub(r'([a-z])\1{2,}',r'\1',temp1)
    # inserting a space between one or two digit numbers and alphabets. Helps for spelling correction.
    # if this is not done, 6gb ram --> kgb ram
    temp3 = re.sub(r'\b(\d{1,2})([a-z])',r'\1 \2',temp2)
    # replacing the repeated symbols .,? by their single symbol where they occur more than once
    # this will help tokenize the sentence using the periodFilter function (called in the sent_tokenize function)
    temp4 = re.sub(r'([.,?])\1+',r'\1',temp3)

    # ----------------TRANSLATION SECTION---------------------
    detected = translator.detect(temp4)
    if detected.lang!='en' and detected.confidence>=0.5:
        trans_text = translator.translate(temp4).text
        # translated sentences don't need spelling correction
        return trans_text
    
    # -----------------SPELLING CORRECTON--------------------
    # making a list of all words (alphanumeric) in the sentence
    words = re.findall(r'\w+',temp4)
    # making a list of all those words that the spellchecker finds suspicious
    misspelled = spell.unknown(words)
    # replacing each suspicious word with its corrected word one by one
    for word in misspelled:        
        temp4 = re.sub(word,spell.correction(word),temp4)    
    return temp4

def sent_tokenize(review):
    '''The nltk.sent_tokenize function misses to break off a sentence at some places
    (for example when the review is in points). Hence, to make it case specific, this is a custom
    made sentence tokenizer which adds onto the capability of nltk's tokenizer.'''
    # The nltk tokenizer considers the 'Rs. ' period symbol as a full stop if it is followed by a space.
    # Hence, replacing 'Rs. ' with 'Rs.' will save the review from mistokenizing
    # Consider this a part of preprocessing that is needed before the tokenization
    review = re.sub(r'(?<=rs\.) ','',review,flags=re.I)
    tok_sents = nltk.sent_tokenize(review) 
    temp = []
    # the period symbol requires special attention because of its variety of uses
    for tok_sent in tok_sents:
        temp_div_sents = periodFilter(tok_sent)
        for div_sent in temp_div_sents:
            temp.append(div_sent)
    result = []
    # tokenizing using other symbols (newline and a question mark)
    for sent in temp:
        div_sents = re.split(r'[\n?]+',sent)
        for sent in div_sents:
            if sent=='':
                continue
            result.append(sent)
    return result

def periodFilter(text):
    '''A recursive function to split sentences when a genuine full stop (with or without a following whitespace) is encountered.
    It does not take into consideration the periods occuring in abbreviations like R.A.M.'''
    match = re.search(r'\w{2}(\.)\w',text)
    split_list = []
    if match is not None:
        pos = match.start(1)
        split_list += [text[:pos]] + periodFilter(text[pos+1:])
        return split_list
    else:
        return [text]

# This is the adjectiviser of the component classifier
def adjectivize(fragment,keyword_obj,tree):
    '''This function attaches adjectives with the matches in keyword_obj and also
    acts as a checking mechanism for the presence of a match.
    The fragment object (in the function arguments) is needed only to add the unidentified noun words to the list'''
    if keyword_obj.matches is None:
        return False
    describing_words = []
    describing_word = []
    # This list will eventually contain all the nouns in the tree    
    unid_nouns_list = []
    matched_flag = False
    chunkfilter = lambda e:e.height()<=2 and re.search(r'NP[ABC]',e.label()) is not None
    # now we will go through every match (of keyword_obj) in every chunk to find the adjectives related to the keyword
    for chunk in tree.subtrees(filter = chunkfilter):
        pos_tagged_words = dict(chunk.leaves())
        for match in keyword_obj.matches:
            if match in pos_tagged_words:
                # just to indicate that there exists at least one match of this keyword in at least one chunk
                # whether or not it has any adjectives attached to it
                if not matched_flag:
                    matched_flag = True
                for word,tag in pos_tagged_words.items():
                    if re.search('RB.?|JJ.?',tag) is not None and validateAdjective(word):
                        describing_word.append(word)
                # if adjectives/adverbs were found, append them to the list
                if len(describing_word)!=0:
                    describing_words.append(' '.join(describing_word))
                    describing_word.clear()
        # Right here, we are simply adding all the nouns (including identified ones) to the list.        
        for word,tag in pos_tagged_words.items():
            if re.search('NN.?',tag) is not None and word not in unid_nouns_list:
                unid_nouns_list.append(word)
    # Here we will filter out all the nouns which belong to THIS keyword's matches, but the nouns of other
    # keywords which may be present in the text will be retained.
    # There is another function called cleanUnidNps that will finally do the cleaning.
    fragment.unid_nps += [noun for noun in unid_nouns_list if noun not in keyword_obj.matches + fragment.unid_nps]
    if len(describing_words)!=0:
        keyword_obj.adjectives += [word for word in describing_words if word not in keyword_obj.adjectives]
    return matched_flag

# THIS FUNCTION CAN BE REFINED
def validateAdjective(adjective):
    'This is just a simple function to apply conditions to the adjectives found.'
    if re.search(r'\d',adjective):
        return False
    elif len(adjective)<=2:
        return False
    else:
        return True

def splitByCC(text,collector,splitparser):
    '''This function splits the text by using coordinating conjunctions and commas as separators/splitters.
    The reultant list is deposited into the collector. This list has the splitters (CCs and commas) inserted
    in between the non-splitters (the usual text), so the splitters and non-splitters will always alternate in the list.'''
    tree = splitparser.parse(nltk.pos_tag(nltk.word_tokenize(text)))
    cc_found_flag = False
    # a list to maintain record of separators to make sure they aren't repeated
    separator_list = []
    splits = [text]
    # for every new CC found, the following loop will iterate through the list of sentences separated
    # by the previous CC and store the further dissected fragments in a new list called splits
    for chunk in tree.subtrees(filter = lambda e:e.label()=='BREAK'):
        if not cc_found_flag:
            cc_found_flag = True
        # the separator might be multiple words separated by spaces
        separator = ' '.join([word for (word,tag) in chunk.leaves()])
        # we are only looking for new CCs
        if separator not in separator_list:
            separator_list.append(separator)        
        else:
            continue

        # if the separator is a comma, surrounding it with word boundaries will render it useless
        # so the surround_flag helps us decide this
        surround_flag = re.search(r'\w',separator) is not None

        # splitting starts here
        old_splits = splits.copy()
        # emptying the list to be filled back up by further divided sentences
        splits = []
        for sent in old_splits:
            if surround_flag:
                # sometimes nltk considers the single letter 'n' also as a CC, so word boundary needs to be applied
                splits += re.split('('+surround(separator)+')',sent)
            else:
                splits += re.split('('+separator+')',sent)

    # if any splitting was done, then append them to the collector, otherwise directly add the original text
    if cc_found_flag:
        for sent in splits:
            collector.append(sent.strip())
    else:
        collector.append(text)

def categoryCheck(fragment,tree,collector,text = ''):
    '''This function checks whether any category word is present in the given tree.
    If yes, then it adds the category to the collector list.
    As a parallel side task, it also ADJECTVIZES each category and subcategory as and when these are searched.'''
    chunk_match_flag = False
    for category in fragment.categories:
        # performing the side task of adjectivizing the category
        big_flag = adjectivize(fragment,category,tree)
        for subcategory in category.subcategories:
            # performing the side task of adjectivizing the subcategory
            small_flag = adjectivize(fragment,subcategory,tree)
            # if even a match of one subcategory is detected, it will flag the presence of the category in the subfragment
            if small_flag:
                big_flag = True
                break
        # The collector need not be a fresh empty list.
        # See the merging operation in subfragment() function for an example.
        if big_flag and category.name not in collector:
            collector.append(category.name)
            if not chunk_match_flag:
                chunk_match_flag = True
    # if no category was found in the adjectivization process, then we will search
    # throughout the text, instead of just searching the groups like in the above process
    # If the text argument is empty, it means that the caller doeasn't want to search outside the adjective groups
    if text!='' and not chunk_match_flag:
        # since we don't have to adjectivize like the above process, we need only one flag
        # unlike the above process which required small_flag and big_flag
        present_flag = False
        for category in fragment.categories:
            for match in category.matches:
                present_flag = match in text
            # if the presence flag is raised, add the category to the list and move on to searching the next category
            if present_flag and category.name not in collector:
                collector.append(category.name)
                continue
            # if the category has not been found, search if the subcategory words are present in the text
            for subcategory in category.subcategories:
                for match in subcategory.matches:
                    present_flag = match in text
                if present_flag and category.name not in collector:
                    collector.append(category.name)
                    break

def cleanUnidNps(fragment):
    '''This function filters out the category/subcategory matched words from the unidentified noun phrases list.
    This actually gives meaning to the list's name i.e. it takes out all the identified keywords from the list.'''
    match_list = []
    for category in fragment.categories:
        match_list += category.matches
        for subcategory in category.subcategories:
            match_list += subcategory.matches
    # The match list now consists of all the words which the program identifies, and shouldn't be in the list
    fragment.unid_nps = [word for word in fragment.unid_nps if word not in match_list and word in fragment.text_processed]

def eliminateWrongGroups(fragment):
    '''This function does a full clean of the fragment. It searches each category, subcategory and adjective (and discards the matches
    altogether). The groups which are not contained in the fragment's text are discarded while the others are kept.
    It adds a refreshed list of category objects, NONE OF WHICH CONTAIN THE MATCHED STRINGS'''
    text = fragment.text_processed
    # The fragment.unid_nps list needs to be cleaned before the wrong catrgories/subcategories are eliminated
    cleanUnidNps(fragment)
    new_cat_list = []
    cat_names = []
    index = -1
    for category in fragment.categories:
        for subcategory in category.subcategories:
            for match in subcategory.matches:
                if match in text:
                    if category.name not in cat_names:
                        # in the constructor, here we have the filtering of adjectives
                        new_cat_list.append(Category(category.name,adjectives=[adj for adj in category.adjectives if adj in text]))
                        cat_names.append(category.name)
                        index += 1
                        current_cat_obj = new_cat_list[index]
                    current_cat_obj.subcategories.append(Subcategory(subcategory.name,adjectives=[adj for adj in subcategory.adjectives if adj in text]))
                    # move on and look for the next subcategory
                    break
        # if category is still not added, it may be because none of its subcategries were detected
        # this is the last check where we search the match of the category word itslef
        if category.name not in cat_names:
            for match in category.matches:
                if match in text:
                    new_cat_list.append(Category(category.name,adjectives = [adj for adj in category.adjectives if adj in text]))
                    cat_names.append(category.name)
                    index += 1
    if len(new_cat_list)==0:
        return False
    # erasing the old categories and replacing them with the new ones
    del fragment.categories
    fragment.categories = new_cat_list
    return True

# First pass of the fragmentiser
def firstPass(tok_sents):
    '''This function looks for independent subcategories in the tokenized
    sentences and maps them back to their categories, hence producing
    fragments with categories as well as subcategories'''

    list_path = os.path.join(dir_path,'ind_subcats.json')
    with open(list_path,'r') as handle:
        ind_component_list = json.load(handle)

    # This list of Fragment objects will be returned by the function
    fragments = []
    # This dictionary will contain the matched subcategories and their matches, and will
    # act as a carrier to load values into the Subcategory class constructor later
    matched_subcategories = dict()
    # This list will maintain the categories reverse mapped by the matched subcategories
    category_list = []
    for sentence in tok_sents:
        parse_sentence = preprocess(sentence)
        for category in ind_component_list:
            # Retrieving the regular expressions corresponding to this category
            # and constructing a big regex out of it using the logical OR '|' regex symbol
            # then conducting a search for it in the text
            match = re.search('|'.join(map(surround,iter(ind_component_list[category]))),parse_sentence)
            pos = 0
            while match is not None:
                # excluding the serializing number from the regex group name (eg. processor1 -> processor)
                subcategory = re.sub(r'([a-z_])\d*',r'\1',match.lastgroup,flags=re.A)
                word = match.group()
                pos = match.start() + pos + 1
                if subcategory not in matched_subcategories:
                    matched_subcategories[subcategory] = [word]
                else:
                    # this covers the case where the same regex has matched more than once for multiple different words
                    # that is, the same word has occured in different forms
                    if word not in matched_subcategories[subcategory]:
                        matched_subcategories[subcategory].append(word)
                # matching for the next iteration
                match = re.search('|'.join(map(surround,iter(ind_component_list[category]))),parse_sentence[pos+1:])
            if len(matched_subcategories)!=0:
                # constructing a category object and appending it to the list
                category_list.append(Category(category,[Subcategory(word,matches.copy()) for (word,matches) in matched_subcategories.items()]))
                matched_subcategories.clear()
        if len(category_list)!=0:
            fragments.append(Fragment(sentence,parse_sentence,category_list.copy()))
            category_list.clear()
        else:
            # for undetected sentances, we construct fragment objects with empty
            # category attribute to be parsed in the second pass (the categorise and subcategorise functions)
            fragments.append(Fragment(sentence,parse_sentence))

    return fragments

# Second pass of the fragmentiser
def categorise(all_fragments):
    '''This function takes all the fragment objects from the review (including
    sentences not detected in the 1st pass) and matches all the category
    keywords that might have been missed in the first pass due to the absence
    of an independent subcategory keyword. All the undetected sentences in this
    pass are discarded.'''

    list_path = os.path.join(dir_path,'categories.csv')
    with open(list_path,'r') as handle:
        csv_reader = reader(handle)
        # This list is a lost of named regular expressions to match the category words
        source_list = list(csv_reader)[0]

    # This list of Fragment objects will be returned by the function
    cat_fragments = []
    for fragment in all_fragments:
        parse_sentence = fragment.text_processed
        categories = fragment.categories
        # Constructing a big regex and searching for it
        match = re.search('|'.join(map(surround,iter(source_list))),parse_sentence)
        pos = 0
        name_list = [categ.name for categ in categories]
        # As soon as a category keyword is found, the group name of the
        # extracted regex is added as one of the categories in the categories list
        while match is not None:
            # excluding the serializing number from the regex group name
            category = re.sub(r'([a-z_])\d*',r'\1',match.lastgroup,flags=re.A)
            word = match.group()
            if category not in name_list:
                # currently filling without subcategories
                # which will be later populated in the subcategorise function
                categories.append(Category(category,matches=[word]))
                name_list.append(category)
            else:
                index = name_list.index(category)
                if word not in categories[index].matches:
                    categories[index].matches.append(word)
            # matching for the next iteration
            pos = match.start() + pos + 1
            match = re.search('|'.join(map(surround,iter(source_list))),parse_sentence[pos+1:])
        if len(categories)!=0:
            cat_fragments.append(fragment)
        # keeping only the fragments who have non-empty a category attribute

    # The fragments will now proceed for attaching the dependent subcategory
    # for every category in the fragment
    return cat_fragments

# Second pass of the fragmentiser
def subcategorise(cat_fragments):
    '''Goes through the categories of every fragment and attaches the
    corresponding dependent subcategories (if found in the text)'''

    list_path = os.path.join(dir_path,'dep_subcats.json')
    with open(list_path,'r') as handle:
        # a dictionary mapping categories to a list of regexes for the corresponding subcategories
        dep_component_list = json.load(handle)

    for fragment in cat_fragments:
        text = fragment.text_processed
        categories = fragment.categories
        for category in categories:
            subcat_names = [subcat.name for subcat in category.subcategories]
            # retrieving all the subcategory regexes corresponding to the
            # category of the fragment and combining them into one large regex
            big_regex = '|'.join(map(surround,iter(dep_component_list[category.name])))
            if big_regex=='':
                continue
            match = re.search(big_regex,text)
            # initialising the position for the parser
            pos = 0
            # As soon as a subcategory keyword is found, the group name of the
            # extracted regex is added as one of the subcategories of the
            # category in the fragment
            while match is not None:
                # excluding the serializing number from the regex group name
                subcategory = re.sub(r'([a-z_])\d*',r'\1',match.lastgroup,flags=re.A)
                word = match.group()
                if subcategory not in subcat_names:
                    category.subcategories.append(Subcategory(subcategory,[word]))
                    subcat_names.append(subcategory)
                else:
                    index = subcat_names.index(subcategory)
                    matches = category.subcategories[index].matches
                    if word not in matches:
                        matches.append(word)

                # matching for the next iteration
                pos = match.start() + pos + 1
                match = re.search('|'.join(map(surround,iter(dep_component_list[category.name]))),text[pos+1:])

# final breakdown of fragments by the fragmentiser
def subfragment(cat_fragments):
    '''Function to further break down the tokenized sentences '''
    # The nltk parsing function's computation time grows very rapidly (>20 mins) near this cutoof length
    SUBFRAGMENTATION_CUTOFF_LENGTH = 28
    main_grammar = r'''
    BREAK: {<CC|,>+}'''
    sub_grammar = r'''NPA: {<DT>?<RB.?>*<JJ.?>+<NN.*?>+}
    NPB: {<DT|CD>?<NN.*?>+<[^,\.]*?>*?<JJ.?><RB.?>?}
    NPC: {<NN.*?>{2,}}'''
    main_parser = nltk.RegexpParser(main_grammar)
    sub_parser = nltk.RegexpParser(sub_grammar)
    # this is the list of subfragments which will be returned by the function
    subfragments = []
    for fragment in cat_fragments:
        split_sents = []
        # splitting the fragment text into a list of non-splitters (normal text), but with
        # a splitter (coordinating conjunctions) in between every non-splitter
        splitByCC(fragment.text_processed,split_sents,main_parser)
        if len(split_sents)==1:
            tree = sub_parser.parse(nltk.pos_tag(nltk.word_tokenize(split_sents[0])))
            # this list is only useful to fulfill the parameter needs of the categoryCheck function
            dummy_list = []
            # using the side effect of categoryCheck to adjectivize the fragment.
            categoryCheck(fragment,tree,dummy_list)
            del dummy_list
            # to maintain uniformity, because other fragments lose their original texts,
            # so these fragments getting the privelege to retain them would be unfair
            fragment.text = fragment.text_processed.strip()                        
            cleanUnidNps(fragment)
            subfragments.append(fragment)
            # The work for this fragment is done. It cannot be divided into subfragments
            continue

        # creating an iterable object to iterate through each group and compare it to the next one
        # adding a padding for the next while loop to work properly
        iterable_sents = iter(['']+split_sents)
        # set of detected categories in the first group
        det_cats_one = []
        # searching for the first significant subfragment
        sent1 = ''
        while len(det_cats_one)==0:
            try:
                # the first text will be a splitter (or a padding) and the second text will be a non-splitter
                sent1 += ' ' + next(iterable_sents) + ' ' + next(iterable_sents)
            except StopIteration as e:
                print(e.__class__,'exception has occured.')
                print('''This error is rare, as it is caused the combined action of failure of regular expressions in our dictionaries
                and the splitting of the text at the wrong point.
                To solve this, kindly see which keywords are there in the fragment and check their regular expressions for loopholes. Please try to eliminate them if you find them.
                Thanks in advance ;)
                EXITING PROGRAM''')
                exit()
            sent1 = sent1.strip()
            tagged_subfragment = nltk.pos_tag(nltk.word_tokenize(sent1))
            if len(tagged_subfragment) > SUBFRAGMENTATION_CUTOFF_LENGTH:
                return cat_fragments
            tree1 = sub_parser.parse(tagged_subfragment)
            categoryCheck(fragment,tree1,det_cats_one,sent1)
        subfragment1 = fragment.copy()
        # the fragment will now lose its original text, and the text field now contains the processed text
        subfragment1.text = sent1
        # clearing off all the categories/subcategories/unidentified noun phrases which are not there in the new text
        eliminateWrongGroups(subfragment1)
        subfragments.append(subfragment1)

        # now, our detected categories list is ready to be compared to the next group (which was separated by a coordinating conjunction)
        while True:
            try:
                # the first text will be a splitter (or a padding) and the second text (sent2) will be a non-splitter
                splitter = next(iterable_sents)
                sent2 = next(iterable_sents)
                tagged_subfragment = nltk.pos_tag(nltk.word_tokenize(sent2))
                if len(tagged_subfragment) > SUBFRAGMENTATION_CUTOFF_LENGTH:
                    return cat_fragments
                tree2 = sub_parser.parse(tagged_subfragment)
                # set of detected categories in the second group
                det_cats_two = []
                # as a rule of the subfragmentation algo, the second fragments must be searched only inside the noun phrases
                # this is why the last argument of categoryCheck is left empty, to disable outside searching
                categoryCheck(fragment,tree2,det_cats_two)

                # if any of the lists is empty, the fragments are not independent
                if len(det_cats_one)==0 or len(det_cats_two)==0:
                    # merging operation
                    # getting the index of the last fragment
                    index = len(subfragments) - 1
                    subfragments[index] = fragment.copy()
                    # simply merging the two fragments won't work because the
                    # second one hasn't been searched outside the noun phrase
                    sent1 += ' ' + splitter + ' ' + sent2
                    subfragments[index].text = sent1                    
                    eliminateWrongGroups(subfragments[index])
                    tagged_subfragment = nltk.pos_tag(nltk.word_tokenize(sent1))
                    if len(tagged_subfragment) > SUBFRAGMENTATION_CUTOFF_LENGTH:
                        return cat_fragments
                    tree1 = sub_parser.parse(tagged_subfragment)
                    # since the last argument was not given the last time, there might have been some identifiable words
                    # that were out of the noun phrases in sent2
                    # this is why we need to update det_cats_one with another category check
                    categoryCheck(fragment,tree1,det_cats_one,sent1)
                    continue

                # Now, the categories captured in both the adjacent groups are ready to be compared.
                # The fragment will be broken into subfragments only if there is no common category in these lists
                common_flag = False
                for find_category in det_cats_one:
                    if find_category in det_cats_two:
                        common_flag = True
                        break

                if not common_flag:
                    # it's time to split
                    subfragment2 = fragment.copy()
                    # note that the splitter in conj is discarded if the fragments are independent
                    subfragment2.text = sent2
                    eliminateWrongGroups(subfragment2)
                    subfragments.append(subfragment2)
                    # the second group will now become our first group  
                    # so det_cats_one will now contain categories from sent2, with external searching enabled
                    # that is, the last argument is given to the function
                    categoryCheck(fragment,tree2,det_cats_one,sent2)
                    sent1 = sent2
                    subfragment1 = subfragment2
                    del subfragment2,sent2

                else:
                    # merging operation
                    # getting the index of the last fragment
                    index = len(subfragments) - 1
                    subfragments[index] = fragment.copy()
                    # simply merging the two fragments won;t work because the
                    # second one hasn't been searched outside the noun phrase
                    sent1 += ' ' + splitter + ' ' + sent2
                    subfragments[index].text = sent1
                    eliminateWrongGroups(subfragments[index])
                    tagged_subfragment = nltk.pos_tag(nltk.word_tokenize(sent1))
                    if len(tagged_subfragment) > SUBFRAGMENTATION_CUTOFF_LENGTH:
                        return cat_fragments
                    tree1 = sub_parser.parse(tagged_subfragment)
                    categoryCheck(fragment,tree1,det_cats_one,sent1)
                    # our new fragment1 is now ready to be compared to the next subfragemnt

            # This exception will be raised when no more items are left in the iterable
            except StopIteration:
                break
    return subfragments

def organize(review):

    # 1st pass: parsing for independent subcategory words
    fragments = firstPass(sent_tokenize(review))
    # 2nd pass:
    # labelling each fragment with the categories that were missed in 1st pass
    cat_fragments = categorise(fragments)
    # associating subcategories (including the dependent subcategories missed in 1st pass) with the corresponding categories
    subcategorise(cat_fragments)
    # categorisation ends here

    final_fragments = subfragment(cat_fragments)

    # This part is only for displaying the output
    '''for fragment in final_fragments:
        print(fragment.text)
        print(fragment.unid_nps)
        categories = fragment.categories
        for category in categories:
            print('Category:',category.name)
            print('Adjectives:',category.adjectives)
            for subcategory in category.subcategories:
                print('\tSubcategory:',subcategory.name)
                print('\tAdjectives:',subcategory.adjectives)
        print('-----------------------------------------------------------------')'''
    return (final_fragments)

'''with open('test.txt','r',encoding='utf-8') as source:
    review = source.read()
organize(review)'''