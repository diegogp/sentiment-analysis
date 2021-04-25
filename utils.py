# import spacy
from liwc import Liwc
import emoji
import nltk
import sqlite3
import pandas as pd
# from enelvo.normaliser import Normaliser
import re
import json
import string
import unicodedata
# function to return key for any value


def get_key(classes, my_dict):
    keys = []
    for _class in classes:
        for key, value in my_dict.items():
            if _class == value:
                keys.append(key)

    return " ".join(keys)


# def pos_tagger(text):
#     doc = nlp(text)
#     pos_tagging_dict = {}
#     for token in doc:
#         pos_tagging_dict[token.text] = token.pos_
#     return pos_tagging_dict


# def lemmatize(text):
#     doc = nlp(text)
#     lemma_list = []
#     for token in doc:
#         lemma_list.append(token.lemma_)
#     return " ".join(lemma_list)


def tokenize(text):
    tokens = nltk.tokenize.word_tokenize(text, language="portuguese")
    return tokens


def remove_stopwords(text):
    tokens = tokenize(text)
    tokens = [token for token in tokens if token not in stopwords]
    text = " ".join(tokens)
    return text


def remove_emoji(text):
    allchars = [str for str in text]
    emoji_list = [c for c in allchars if c in emoji.UNICODE_EMOJI["pt"]]
    text = ' '.join([str for str in text.split()
                    if not any(i in str for i in emoji_list)])
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    return text


def remove_tags(text):
    pattern = r"@[a-zA-Z0-9]+"
    text = re.sub(pattern, "", text)
    return text


def remove_hashtags(text):
    pattern = r"#[a-zA-Z0-9]+"
    text = re.sub(pattern, "", text)
    return text


def lowercase(text):
    text = text.lower()
    return text


def remove_quotes(text):
    text = re.sub(r"""['"]+""", "", text)
    return text


def remove_urls(text):
    text = re.sub(r"(?:\@|http?\://|https?\://|www)\S+", "", text)
    return text


def remove_punctuation(text):
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text


def remove_double_spaces(text):
    text = re.sub("\s\s+", " ", text)
    text = text.strip()
    return text


def remove_quotes_marks(text):
    text = text.replace('"', "")
    text = text.replace("'", "")
    return text


def remove_digits(text):
    remove_digits_trans = str.maketrans('', '', string.digits)
    text = text.translate(remove_digits_trans)
    return text


def get_liwc_analysis(text):
    liwc = Liwc(LIWCLocation)
    tokens = tokenize(text)
    liwc_analysis = dict(liwc.parse(tokens))
    return liwc_analysis


def check_subjectivity(liwc_analysis):
    classes = ['compare (Comparisons)',
               'affect (Affect)',
               'posemo (Positive Emotions)',
               'negemo (Negative Emotions)']
    for class_ in classes:
        if class_ in liwc_analysis:
            return 1
    return 0


def remove_non_ascii_normalized(text):
    normalized = unicodedata.normalize('NFD', text)
    text = normalized.encode('ascii', 'ignore').decode('utf8')
    return text
    
def truncate_ellipsis(text):
    if text.endswith("…"):
        text = " ".join(text.split(" ")[:-1])
    return text

# def normalize(text):
    # normalizer = Normaliser()
    # text = normalizer.normalise(text)
    # text = text.replace('username', '')
    # text = text.replace('hashtag', '')
    # text = text.replace('number', '')
    # text = text.replace('url', '')
    # return text


def preprocess(df):
    df['preprocessed_text'] = df.text.apply(remove_urls)
    df['preprocessed_text'] = df.preprocessed_text.apply(lowercase)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_non_ascii_normalized)
    #df['preprocessed_text'] = df.preprocessed_text.apply(lambda x: x.strip())
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_tags)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_hashtags)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_emoji)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_quotes)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_punctuation)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_digits)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_quotes_marks)
    df['preprocessed_text'] = df.preprocessed_text.apply(truncate_ellipsis)
    df['preprocessed_text'] = df.preprocessed_text.apply(remove_double_spaces)

    return df


def main():
    con = sqlite3.connect("tweets.db")
    sql = "select id_str, text from tweets where text not like '%RT @%' order by random() limit 2000"
    df = pd.read_sql(sql, con=con, index_col="id_str")
    df = preprocess(df)
    df['liwc_analysis'] = df.preprocessed_text.apply(get_liwc_analysis)
    df['is_subjective'] = df.liwc_analysis.apply(check_subjectivity)
    # df = filter_dataset_with_sentiment_words(df)
    return df


if __name__ == "__main__":
    # nlp = spacy.load("pt_core_news_sm")
    # stopwords = nltk.corpus.stopwords.words('portuguese')
    # nltk.download('punkt')
    # classes = ['VERB', 'NOUN', 'ADJ']
    LIWCLocation = 'LIWC2015.dic'
