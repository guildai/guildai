import os

from datetime import datetime

import tensorflow as tf
import tensorflow_datasets as tfds
from tensorboard.plugins import projector

train_epochs = 1
validation_steps = 20

(train_data, test_data), info = tfds.load(
    "imdb_reviews/subwords8k",
    split=(tfds.Split.TRAIN, tfds.Split.TEST),
    with_info=True,
    as_supervised=True,
)
encoder = info.features["text"].encoder

# shuffle and pad the data.
train_batches = train_data.shuffle(1000).padded_batch(10, padded_shapes=((None,), ()))
test_batches = test_data.shuffle(1000).padded_batch(10, padded_shapes=((None,), ()))
train_batch, train_labels = next(iter(train_batches))

# Create an embedding layer
embedding_dim = 16
embedding = tf.keras.layers.Embedding(encoder.vocab_size, embedding_dim)
# Train this embedding as part of a keras model
model = tf.keras.Sequential(
    [
        embedding,  # The embedding layer should be the first layer in a model.
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(1),
    ]
)

# Compile model
model.compile(
    optimizer="adam",
    loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
    metrics=["accuracy"],
)

# Train model
history = model.fit(
    train_batches,
    epochs=train_epochs,
    validation_data=test_batches,
    validation_steps=validation_steps,
)

# Set up a logs directory, so Tensorboard knows where to look for files
log_dir = os.getenv("LOGDIR") or "logs/imdb-example/" + datetime.now().strftime(
    "%Y%m%d-%H%M%S"
)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Save Labels separately on a line-by-line manner.
with open(os.path.join(log_dir, 'metadata.tsv'), "w") as f:
    for subwords in encoder.subwords:
        f.write("{}\n".format(subwords))
    # Fill in the rest of the labels with "unknown"
    for unknown in range(1, encoder.vocab_size - len(encoder.subwords)):
        f.write("unknown #{}\n".format(unknown))


# Save the weights we want to analyse as a variable. Note that the first
# value represents any unknown word, which is not in the metadata, so
# we will remove that value.
weights = tf.Variable(model.layers[0].get_weights()[0][1:])
# Create a checkpoint from embedding, the filename and key are
# name of the tensor.
checkpoint = tf.train.Checkpoint(embedding=weights)
checkpoint.save(os.path.join(log_dir, "embedding.ckpt"))

# Set up config
config = projector.ProjectorConfig()
embedding = config.embeddings.add()
# The name of the tensor will be suffixed by `/.ATTRIBUTES/VARIABLE_VALUE`
embedding.tensor_name = "embedding/.ATTRIBUTES/VARIABLE_VALUE"
embedding.metadata_path = 'metadata.tsv'
projector.visualize_embeddings(log_dir, config)
