import pandas as pd

fhand = open('galaxy_m40.txt','r',encoding='utf-8')

data = pd.DataFrame(columns=['model_name','review'])

counter = 0
index = 0
review = ''
for line in fhand:
    if line=='-----\n':
        counter += 1
        if counter%2==0:
            del review
            review = ''
    elif counter%2==0:
        review += line
    else:
        data.loc[index] = ['Samsung Galaxy M40',review]
        index += 1
        if index%100==0:
            print(index,'reviews loaded')
            #if index==1200:
            #    break

data.to_csv('galaxy_m40.csv',index=False)