import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub

from sklearn.preprocessing import MultiLabelBinarizer


def categorize(words):
    # nn stuff
    return ['politics', 'captain']


data = pd.DataFrame({
    'text': [
        '''Led by Woody, Andy's toys live happily in his room until Andy's birthday brings Buzz Lightyear onto the scene. Afraid of losing his place in Andy's heart, Woody plots against Buzz. But when circumstan...''',
        '''When siblings Judy and Peter discover an enchanted board game that opens the door to a magical world, they unwittingly invite Alan -- an adult who's been trapped inside the game for 26 years -- into t...''',
        '''A family wedding reignites the ancient feud between next-door neighbors and fishing buddies John and Max. Meanwhile, a sultry Italian divorcée opens a restaurant at the local bait shop, alarming the l...'''],
    'categories': [
        ['Adventure', 'Fantasy', 'Family'],
        ['Romance', 'Comedy'],
        ['Comedy', 'Drama', 'Romance']
    ]
}, columns=['text', 'categories'])

text = data['text']
categories = data['categories']

encoder = MultiLabelBinarizer()
encoder.fit_transform(categories)
train_encoded = encoder.transform(categories)
num_classes = len(encoder.classes_)

multi_label_head = tf.contrib.estimator.multi_label_head(
    num_classes,
    loss_reduction=tf.losses.Reduction.SUM_OVER_BATCH_SIZE
)

# takes time
text_embeddings = hub.text_embedding_column(
    "text",
    module_spec="https://tfhub.dev/google/universal-sentence-encoder/2",
    trainable=False
)

# Format our data for the numpy_input_fn
features = {
    "text": np.array(text).astype(np.str)
}
labels = np.array(train_encoded).astype(np.int32)

train_input_fn = tf.estimator.inputs.numpy_input_fn(
    features,
    labels,
    shuffle=False,
    batch_size=32,
    num_epochs=20
)

estimator = tf.estimator.DNNEstimator(
    head=multi_label_head,
    hidden_units=[64, 10],
    feature_columns=[text_embeddings]
)

estimator.train(input_fn=train_input_fn)

#############################
raw_test = [
    "An examination of our dietary choices and the food we put in our bodies. Based on Jonathan Safran Foer's memoir.",
    # Documentary
    "A teenager tries to survive the last week of her disastrous eighth-grade year before leaving to start high school.",
    # Comedy
    "Ethan Hunt and his IMF team, along with some familiar allies, race against time after a mission gone wrong."
    # Action, Adventure
]

predict_input_fn = tf.estimator.inputs.numpy_input_fn({'text': np.array(raw_test).astype(np.str)},
                                                      shuffle=False)
results = estimator.predict(predict_input_fn)

for movie_genres in results:
    top_2 = movie_genres['probabilities'].argsort()[-2:][::-1]
    for genre in top_2:
        text_genre = encoder.classes_[genre]
        print(text_genre + ': ' + str(round(movie_genres['probabilities'][genre] * 100, 2)) + '%')
