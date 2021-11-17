import os
import pickle
from collections import Counter

import Filepaths as F
import Utils
import nltk
import string
import numpy as np
import pandas as pd

from Utils import Column, UNK_TOKEN


def get_article_indices(article_tokens, vocabulary_ls):
    indices_ls = []
    for tok in article_tokens:
        try:
            idx = vocabulary_ls.index(tok)
        except ValueError:
            idx = vocabulary_ls.index('unk')
        indices_ls.append(idx)
    return indices_ls

# Iterator that gives an article's vocabulary indices and class label
def next_featuresandlabel_article(corpus_df):

    vocabulary_ls = get_vocabulary(corpus_df, F.vocabulary_fpath, min_frequency=2, new=False)

    article_labels = get_labels(corpus_df)
    articles_ls = list(corpus_df[Utils.Column.ARTICLE.value])

    for i, article in enumerate(articles_ls):
        # article is a string. E.g.: "21-Jähriger fällt wohl bis Saisonende aus. Wien – Rapid muss wohl bis ..."
        tokens_ls_0 = nltk.tokenize.word_tokenize(article, language='german')
        tokens_ls_lower = [tok.lower() for tok in tokens_ls_0]
        tokens_ls_nopunct = [tok for tok in tokens_ls_lower
                                     if tok not in '"#$%&\'()*+,-/:;<=>@[\\]^_`{|}~']  # keep the hyphen
        article_indices = get_article_indices(tokens_ls_nopunct, vocabulary_ls)

        yield (article_indices, article_labels[i])


# From the original training corpus in train.csv, split off 10% to be the validation set,
# and keep the rest in Models/training.csv to be used as the actual training set
def organize_training_corpus(train_corpus_df):


    new_training_rows_ls = []
    validation_rows_ls = []

    num_articles = train_corpus_df.index.stop
    random_assignment_arr = np.random.rand(num_articles)
    validation_threshold = 0.9

    for index, row in train_corpus_df.iterrows():
        if random_assignment_arr[index] > validation_threshold:
            validation_rows_ls.append(row)
        else:
            new_training_rows_ls.append(row)

    new_training_df = pd.DataFrame(new_training_rows_ls)
    validation_df = pd.DataFrame(validation_rows_ls)

    new_training_df.to_csv(F.training_set_file, index=False, sep=";", header=False)
    validation_df.to_csv(F.validation_set_file, index=False, sep=";", header=False)

    return (new_training_df, validation_df)


# Retrieves the vocabulary, or creates it if not present
# Source: train.csv. Tokenizer: NLTK's word_tokenize(language='german'). Default: lowercase
def get_vocabulary(corpus_df, vocab_fpath, min_frequency, new=False, lowercase=True):

    if os.path.exists(vocab_fpath) and not new:
        with open(vocab_fpath, "rb") as vocab_file:
            vocabulary_ls = pickle.load(vocab_file)
    else:
        articles = corpus_df[Column.ARTICLE.value].to_list()
        vocabulary_counter = Counter()

        for article in articles:
            words = nltk.tokenize.word_tokenize(article, language='german')
            if lowercase:
                words = [w.lower() for w in words]
            vocabulary_counter.update(words)

        vocabulary_ls_0 = list(vocabulary_counter.keys())
        vocabulary_ls = [w for w in vocabulary_ls_0 if vocabulary_counter[w] >= min_frequency]
        if UNK_TOKEN not in vocabulary_ls:
            vocabulary_ls.append(UNK_TOKEN)
        with open(vocab_fpath, "wb") as vocab_file:
            pickle.dump(vocabulary_ls, vocab_file)

    return vocabulary_ls


def get_labels(split_df):
    class_names = list(split_df["class"].value_counts().index)
    labels_ls = []
    for index, row in split_df.iterrows():
        labels_ls.append(class_names.index(row["class"]))

    return labels_ls