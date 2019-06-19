from sklearn.manifold import TSNE
import pandas as pd
import altair as alt
import pickle
import numpy as np
from pymongo import MongoClient
from src import MONGOPATH


def read_mongo(collection, query={}, noid=True):

    cursor = MongoClient(MONGOPATH).RECIPES[collection].find(query)
    df = pd.DataFrame(list(cursor))
    if noid:
        del df['_id']
    df['vector'] = df['vector'].apply(pickle.loads)

    return df


def t_sne(df):

    X = df['vector'].values
    X_train = np.vstack(X)
    X_embedded = TSNE(n_iter=5000).fit_transform(X_train)
    df['tsne_dim1'] = X_embedded[:, 0]
    df['tsne_dim2'] = X_embedded[:, 1]
    return df


def plot_tsne(df):

    chart = alt.Chart(df).mark_circle(size=60).encode(
        x='tsne_dim1:Q',
        y='tsne_dim2:Q',
        tooltip='title:N'
    ).interactive()

    chart.serve()

