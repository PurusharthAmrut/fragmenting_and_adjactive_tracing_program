import re

def makeRegex(word_list,name):
    '''This function takes a list of word forms and constructs a
    regular expression to accomodate all these words'''
    regex = list(min(word_list))
    index = len(regex) - 1
    prev_index = index + 1
    while prev_index!=index:
        prev_index = index
        for word in word_list:
            if word[index]!=regex[index]:
                del regex[index]
                index -= 1
                break

    accomodation = len(max(word_list,key=len)) - len(regex)
    # the group name of the regex must be a proper python identifier    
    regex.append('\\w{,'+str(accomodation)+'})')
    regex.insert(0,'(?P<'+name+'>')
    return ''.join(regex)

words = ['heating','heated','heat','heats']
print(makeRegex(words,'heating'))
