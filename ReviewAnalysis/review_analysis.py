from pymongo import MongoClient
from pprint import pprint
import sys
from datetime import datetime
import pytz

pytz.timezone('Asia/Kolkata')

# Importing local packages
from Neural_Nets.cnn_lstm_predict import cnn_lstm_predict
from Text_Preprocessors.nat_program import organize
from Text_Preprocessors.ReviewClass import Fragment, Category, Subcategory
from Text_Preprocessors.text_preprocessor import text_tokenizer_without_stem

client = MongoClient(port = 27017)
db = client.samsung_reviews

def attach_sentiment(review_fragments):
    '''
    Takes the fragment class as input and then attaches the sentiment
    using the specified NN model.
    '''
    for fragment in review_fragments:
        fragment.sentiment = cnn_lstm_predict(fragment.text)
    return review_fragments

def counter_autoincrement(field, qty=1):
    '''
    This functions is used to update the serial count of new entries to
    the database, using the counter collection.\n
    field: Takes the argument for the field to be autoincremented. Available
    options are - 'review_count', 'category_count', 'subcategory_count',
    'unidentified_np_count'.\n
    qty: This takes an integer as an argument, and is the amount by which
    field's count should be incremented. Default value : 1.
    '''
    if type(qty) is not int:
        sys.exit("TypeError:\n \
            Expected an integer in qty field, instead got " + str(type(qty)))

    db.counter.update_one({},{'$inc':{field:qty}})
    updated_count = db.counter.find()
    return updated_count[0][field]

def fetch_id(frag_param, value):
    '''
    This function returns the id of the specified field.
    frag_param: The parameter for which id is to be fetched. Options are:
    1. 'category'; 2. 'subcategory'; 3. 'unid_id'\n
    value: Takes the value of the parameter for which id was fetched.\n
    \t If the value entry doesn't exist in the database then a new document
    entry is created and its assigned id is returned.
    '''

    if frag_param == 'category':
        query = db.categories.find_one({'category_name':value})
        if query is not None:
            db.categories.update_one({'category_name':value},{'$inc':{'cat_freq':1}})
            return query['category_id']
        else:
            category_id = counter_autoincrement('category_count')
            db.categories.insert_one({
                'category_id': category_id,
                'category_name': value,
                'cat_freq':1
            })
            return category_id

    elif frag_param == 'subcategory':
        query = db.subcategories.find_one({'subcategory_name':value})
        if query is not None:
            db.subcategories.update_one({"subcategory_name":value},{'$inc':{"subcat_freq":1}})
            return query['subcategory_id']
        else:
            subcategory_id = counter_autoincrement('subcategory_count')
            db.subcategories.insert_one({
                'subcategory_id': subcategory_id,
                'subcategory_name': value,
                'subcat_freq':1
            })
            return subcategory_id
    
    elif frag_param == 'unid_np':
        query = db.unidentified_np.find_one({'unid_np_name':value})
        if query is not None:
            db.categories.update_one({"unid_np_name":value},{'$inc':{"unid_np_freq":1}})
            return query['unid_np_id']
        else:
            unid_np_id = counter_autoincrement('unidentified_np_count')
            db.unidentified_np.insert_one({
                'unid_np_id': unid_np_id,
                'unid_np_name': value,
                'unid_np_freq':1
            })
            return unid_np_id
    else:
        sys.exit("""Fatal Error!
        Got an unexpected input. Terminating Program.""")
    

def review_analysis(review):
    '''This function takes the review as input and applies the nat 
    program as well the sentiment analyser. The functionality to choose
    between some of the trained NN models will be added in the future.
    For now the CNN-LSTM network is the default model.
    After analysis the review is stored in MongoDB samsung_reviews
    database.
    '''

    # Applying the NAT algorithm
    review_fragments = organize(review)

    # Attaching sentiments to each of the fragments
    review_fragments = attach_sentiment(review_fragments)
    # Creating the input dictionary to be sent to the DB.
    review_analysed = dict()
    review_analysed['review'] = review
    review_analysed['num_fragments'] = len(review_fragments)

    # Retrieving the counter collection. The counter collection maintains
    # a serial count of the elements in all of the data collections.
    review_analysed['date_added'] = datetime.utcnow()
    review_analysed['review_no'] = counter_autoincrement('review_count')
    fragment_list = []
    frag_details = []
    frag_data = dict()
    frag_params = dict()
    count = 0
    for fragment in review_fragments:
        count += 1
        frag_data['frag_text'] = fragment.text
        frag_data['frag_no'] = count
        frag_data['unid_np'] = fragment.unid_nps.copy()
        if len(frag_data['unid_np']) > 0:            
            frag_data['unid_np_present'] = True
        else:            
            frag_data['unid_np_present'] = False
            
        fragment_list.append(frag_data.copy())

        category_list = fragment.categories
        for category in category_list:
            frag_params['category'] = category.name
            frag_params['subcategory'] = [subcat.name for subcat in category.subcategories]
            frag_params['cat_id'] = fetch_id('category', category.name)
            frag_params['subcat_id'] = [fetch_id('subcategory',subcat) for subcat in frag_params['subcategory']]
            frag_params['sentiment'] = fragment.sentiment
            frag_params['adjective'] = []
            for subcat in category.subcategories:
                frag_params['adjective'] += subcat.adjectives
            frag_params['adjective'] += category.adjectives
            frag_params['frag_no'] = count
            frag_details.append(frag_params.copy())
        frag_params.clear()
        frag_data.clear()
    review_analysed['fragments'] = fragment_list
    review_analysed['frag_details'] = frag_details
    review_analysed['tokens'] = text_tokenizer_without_stem(review)
    db.reviews_data.insert_one(review_analysed)
    return review_analysed
