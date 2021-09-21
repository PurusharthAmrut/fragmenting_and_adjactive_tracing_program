from nat_program import organize
from ReviewClass import Fragment
import pandas as pd

#labelled_data = pd.DataFrame(columns = ['Review','Sentiment','ReviewType','counter_value'])
labelled_data = pd.read_csv('manually_labelled_dataset.csv')
print(labelled_data.head())

sentiments = ['very negative','negative','neutral','positive','very positive']
#review_types = ['review','QnA','error','suggestion','other']
valid_list = [0,1,2,3,4]
last_index = len(labelled_data.index)-1
if last_index>=0:
    last_count = labelled_data.loc[last_index].counter_value
    last_frag_count = labelled_data.loc[last_index].frag_count
else:
    last_count = -1
    last_frag_count = -1

fhand = open('extract_with_rating.txt','r',encoding='utf-8')

index = last_index + 1
counter = 0
resume_flag = True
review = ''
try:
    for line in fhand:

        if counter <= last_count-2:
            if line=='-----\n':
                counter += 1
            continue

        elif line=='-----\n':
            counter += 1
            if counter%2==0:
                del review
                review = ''
        elif counter%2==0:
            review += line
        else:
            fragments = organize(review)
            if resume_flag and last_frag_count==len(fragments)-1:
                resume_flag = False
                continue
            frag_count = -1
            for fragment in fragments:
                frag_count += 1
                if resume_flag and frag_count<=last_frag_count:
                    continue
                if resume_flag:
                    resume_flag = False
                print('\n'+fragment.text_processed)
                senti_index = int(input('Sentiment: '))
                while senti_index not in valid_list+[8,9]:
                    print('INVALID RESPONSE')
                    senti_index = int(input('Sentiment: '))
                if senti_index in valid_list:
                    print('...'+sentiments[senti_index])
                elif senti_index==8:
                    continue
                else:
                    print('TERMINATE')
                    labelled_data.to_csv('manually_labelled_dataset.csv',index=False)
                    exit()
                '''type_index = int(input('Review Type: '))
                while senti_index not in valid_list:
                    print('INVALID RESPONSE')
                    type_index = int(input('Review Type: '))
                print('...'+review_types[type_index])'''
                labelled_data.loc[index] = [fragment.text_processed,senti_index,5,counter,frag_count]
                index += 1
except SystemExit:
    print('Program terminated')
finally:
    labelled_data.to_csv('manually_labelled_dataset.csv',index=False)
    fhand.close()