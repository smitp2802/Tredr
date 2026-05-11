import pandas as pd


def clean_dataframe(df):

    df = df.dropna()

    df = df.sort_index()

    return df
