class Noun:
    def __init__(self,word,match,adjectives = None):
        self.word = word
        self.match = match
        self.adjactives = adjectives

class Fragment:
    def __init__(self,text,text_processed,categories):
        self.text = text
        self.text_processed = text_processed
        # categories and subcategories are lists of Noun objects
        self.categories = categories
