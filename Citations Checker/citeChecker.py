import pandas as pd
import re
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from joblib import load
from stop_words import get_stop_words
from sklearn.preprocessing import LabelEncoder

knn_model_lem_count_vec = load('Citations Checker\knn_model_lem_count_vec.joblib')

df = pd.read_csv('Citations Checker\legal_text_classification.csv')

df['case_text_sum'] = df["case_title"] + " " + df["case_text"]

df['case_text_sum'] = df['case_text_sum'].fillna(
    '')  # Fill NaN values with empty string
mask = df["case_text_sum"].str.contains(r"https?://\S+|www\.\S+")
res = df.loc[mask]

def cleaning(inp_str):
    marks = '''!()-[]{};?@#$%:'"\,|./^&;*_1234567890'''
    inp_str = inp_str.lower()
    inp_str = inp_str.replace(r'https?://\S+|www\.\S+', '')
    for x in inp_str:
        if x in marks:
            inp_str = inp_str.replace(x, "")
    inp_str = inp_str.replace('url', '').replace('privacy policy', '')\
                     .replace('disclaimers', '').replace('disclaimer', '').replace('copyright policy', '')
    return inp_str


def beauty_df(df, col='case_text_sum'):
    return df[col].apply(lambda x: cleaning(x)).str.split().apply(lambda x: " ".join(x))


def split_df(df, col='case_text_sum', beauty=True):
    if beauty:
        return beauty_df(df, col).str.split()
    else:
        df[col].str.split()


def df_to_dict_unique(df, col='case_text_sum'):
    a = dict()
    df = split_df(df, 'case_text_sum')
    for i in df:
        for j in i:
            if j not in a.keys():
                a[j] = 0
            else:
                a[j] += 1
    return a


le = LabelEncoder()
df['case_outcome_num'] = le.fit_transform(df.case_outcome)

stop_words = get_stop_words('en')

splited_df = split_df(df, col='case_text_sum', beauty=True)

wsw = splited_df.apply(
    lambda x: [i for i in x if i not in stop_words and len(i) > 2])

def get_lem_word(word):
    wnl = WordNetLemmatizer()
    return wnl.lemmatize(word, pos="v")

with_lem = wsw.apply(lambda x: [get_lem_word(i) for i in x])

test_lem = with_lem.sort_index().reset_index().drop('index', axis=1)

test_lem_ser = test_lem.case_text_sum

count_vectorizer_lem = CountVectorizer(max_features=2500)

count_vectors_lem = count_vectorizer_lem.fit_transform(
    test_lem_ser.apply(' '.join))

x_test_lem_count_vec = count_vectors_lem.toarray()

count_vectors_lem = count_vectorizer_lem.fit_transform(
    test_lem_ser.apply(' '.join))
x_test_lem_count_vec = count_vectors_lem.toarray()

knn_pred_lem_count_vec = knn_model_lem_count_vec.predict(x_test_lem_count_vec)

print(knn_pred_lem_count_vec)