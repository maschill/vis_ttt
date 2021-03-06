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
    dataset['noOutlier']=True

    for i in num:
        dataset['noOutlier'] = np.where(dataset['noOutlier']==True, \
                                               ((dataset[i]-dataset[i].mean()).abs()/dataset[i].std()<3), False)

    miss = np.where(pd.isnull(dataset))[0]

    dataset['complete'] = True

    warnings.simplefilter('ignore')

    dataset['complete'][miss] = False

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

    for column in dataset:
        if column not in num :
            dataset[column] =  pd.to_datetime(dataset[column], format='%Y-%m-%d %H:%M:%S.%f', errors='ignore')

    return dataset
    

def main():

    ### switch from deleting to marking
    
    dataset=pd.read_csv('../data/data/m_airrsgtc.tsv',sep='\t')

    #dataset=markMissesAndOutliers(dataset)
        #dataset=delMissesAndOutliers(dataset)
        #dataset=replaceMissesMarkOutliers(dataset)

    dataset=timeConv(dataset)

    print(dataset.head())

    #dataset.to_csv('data/data/m_airrsgtc_temp.tsv', header=False, index=False,sep='\t')

if __name__ == "__main__":
    main()
