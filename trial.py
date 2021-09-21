import pandas as pd

data = pd.read_csv('galaxy_m40.csv')
print(data.loc[0].review)