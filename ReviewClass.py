class Subcategory:
    def __init__(self,name,matches = None,adjectives = None):
        self.name = name
        self.matches = matches
        if adjectives is None:
            self.adjectives = []
        else:
            self.adjectives = adjectives

class Category:
    def __init__(self,name,subcategories=None,matches=None,adjectives=None):
        self.name = name
        # subcategories is a list of subcategory objects
        if subcategories is None:
            self.subcategories = []
        else:
            self.subcategories = subcategories

        # subcategories don't need this rule ecause they are always initialised with a match
        if matches is None:
            self.matches = []
        else:
            self.matches = matches
        
        if adjectives is None:
            self.adjectives = []
        else:
            self.adjectives = adjectives
             
    def __len__(self):
        return len(self.subcategories)

    def __getitem__(self,key):
        if key < self.__len__():
            return self.subcategories[key]
        else:
            raise IndexError('Index out of range')
    
    def __setitem__(self,key,new_subcat):
        if key < self.__len__():
            self.subcategories[key] = new_subcat
        else:
            raise IndexError('Index out of range')
    
    def __contains__(self,subcategory):
        return subcategory in [subcat.name for subcat in self.subcategories]
    
    def append(self,subcategory):
        self.subcategories.append(subcategory)

class Fragment:
    def __init__(self,text,text_processed = None,categories = None):
        self.text = text
        self.text_processed = text_processed
        # this shall be a list of category objects
        if categories is None:
            self.categories = []
        else:
            self.categories = categories
        self.sentiment = ''
        self.unid_nps = []
    
    def copy(self):
        return Fragment(self.text,self.text_processed,self.categories.copy())
