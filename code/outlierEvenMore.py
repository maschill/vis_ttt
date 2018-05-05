import pandas as pd
import pandas
import os, sys
import csv, json
from scipy import stats
import numpy as np
import warnings

def delMissesAndOutliers(dataset):
    
    num = dataset.select_dtypes(include=[np.number]).columns.values
    dataset[num]=dataset[num][~((dataset[num]-dataset[num].mean()).abs()>3*dataset[num].std())]

    dataset.dropna(inplace=True)

    return dataset

# first bool column outlier, second misses in row
def markMissesAndOutliers(dataset):

    num = dataset.select_dtypes(include=[np.number]).columns.values
    dataset[dataset.shape[1]]=True

    for i in num:
        dataset[dataset.shape[1]-1] = np.where(dataset[dataset.shape[1]-1]==True, \
                                               ((dataset[i]-dataset[i].mean()).abs()/dataset[i].std()<3), False)

    miss = np.where(pd.isnull(dataset))[0]

    dataset[dataset.shape[1]] = True

    warnings.simplefilter('ignore')

    dataset[dataset.shape[1]-1][miss] = False

    warnings.simplefilter('default')

    return dataset

def replaceMissesMarkOutliers(dataset):

    num = dataset.select_dtypes(include=[np.number]).columns.values
    dataset[dataset.shape[1]]=True

    for i in num:
        dataset[dataset.shape[1]-1] = np.where(dataset[dataset.shape[1]-1]==True, \
                                               ((dataset[i]-dataset[i].mean()).abs()/dataset[i].std()<3), False)

    dataset.fillna(dataset.mode().iloc[0], inplace=True)

    return dataset

def timeConv(dataset):

    num = dataset.select_dtypes(include=[np.number]).columns.values

    cols = dataset.shape[1]
    for i in range(cols):
        if not i in num :
            dataset[i] =  pd.to_datetime(dataset[i],errors='ignore')

    return dataset
    

def main():

    with open('indiabetes.csv', 'rb') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=None, delimiter=',')

    ### switch from deleting to marking
    
    dataset=pd.read_csv('data/data/m_airrsgtc.tsv',header=None,sep='\t')
    #print(dataset.describe())

    dataset=markMissesAndOutliers(dataset)
        #dataset=delMissesAndOutliers(dataset)
        #dataset=replaceMissesMarkOutliers(dataset)

    dataset=timeConv(dataset)

    print dataset.head(10)

    dataset.to_csv('data/data/m_airrsgtc_temp.tsv', header=False, index=False,sep='\t')

if __name__ == "__main__":
    main()
