import argparse
import json

import tensorflow as tf

from tensorflow.examples.tutorials.mnist import input_data

p = argparse.ArgumentParser()
p.add_argument(
    "--datadir", default="data",
    help="Location of MNIST data")
p.add_argument(
    "--rundir", default=".",
    help="Location to write prepared data, logs and checkpoints")
p.add_argument(
    "--batch_size", type=int, default=100,
    help="Batch size used for training")
p.add_argument(
    "--epochs", type=int, default=10,
    help="Number of epochs to train")
p.add_argument(
    "--prepare", dest='just_data', action="store_true",
    help="Just prepare data - don't train")
p.add_argument(
    "--test", action="store_true",
    help="Evaluate a trained model with test data")
FLAGS = p.parse_args()

def init_data():
    global mnist
    mnist = input_data.read_data_sets(FLAGS.datadir, one_hot=True)

def init_train():
    init_model()
    init_train_op()
    init_eval_op()
    init_summaries()
    init_collections()
    init_session()

def init_model():
    global x, y, W, b
    x = tf.compat.v1.placeholder(tf.float32, [None, 784])
    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))
    y = tf.nn.softmax(tf.matmul(x, W) + b)

def init_train_op():
    global y_, loss, train_op
    y_ = tf.compat.v1.placeholder(tf.float32, [None, 10])
    loss = tf.reduce_mean(
             -tf.reduce_sum(
               y_ * tf.math.log(y),
               reduction_indices=[1]))
    train_op = tf.compat.v1.train.GradientDescentOptimizer(0.5).minimize(loss)

def init_eval_op():
    global accuracy
    correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

def init_summaries():
    init_inputs_summary()
    init_variable_summaries(W, "weights")
    init_variable_summaries(b, "biases")
    init_op_summaries()
    init_summary_writers()

def init_inputs_summary():
    tf.compat.v1.summary.image("inputs", tf.reshape(x, [-1, 28, 28, 1]), 10)

def init_variable_summaries(var, name):
    with tf.name_scope(name):
        mean = tf.reduce_mean(var)
        tf.compat.v1.summary.scalar("mean", mean)
        stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.compat.v1.summary.scalar("stddev", stddev)
        tf.compat.v1.summary.scalar("max", tf.reduce_max(var))
        tf.compat.v1.summary.scalar("min", tf.reduce_min(var))
        tf.compat.v1.summary.histogram(name, var)

def init_op_summaries():
    tf.compat.v1.summary.scalar("loss", loss)
    tf.compat.v1.summary.scalar("acc", accuracy)

def init_summary_writers():
    global summaries, train_writer, validate_writer
    summaries = tf.compat.v1.summary.merge_all()
    train_writer = tf.compat.v1.summary.FileWriter(
        FLAGS.rundir, tf.compat.v1.get_default_graph())
    validate_writer = tf.compat.v1.summary.FileWriter(
        FLAGS.rundir + "/val")

def init_collections():
    tf.compat.v1.add_to_collection("inputs", json.dumps({"image": x.name}))
    tf.compat.v1.add_to_collection("outputs", json.dumps({"prediction": y.name}))
    tf.compat.v1.add_to_collection("x", x.name)
    tf.compat.v1.add_to_collection("y_", y_.name)
    tf.compat.v1.add_to_collection("acc", accuracy.name)

def init_session():
    global sess
    sess = tf.compat.v1.Session()
    sess.run(tf.compat.v1.global_variables_initializer())

def train():
    steps = (mnist.train.num_examples // FLAGS.batch_size) * FLAGS.epochs
    for step in range(steps):
        images, labels = mnist.train.next_batch(FLAGS.batch_size)
        batch = {x: images, y_: labels}
        sess.run(train_op, batch)
        maybe_log_accuracy(step, batch)
        maybe_save_model(step)
    save_model()

def maybe_log_accuracy(step, last_training_batch):
    if step % 20 == 0:
        evaluate(step, last_training_batch, train_writer, "training")
        validate_data = {
            x: mnist.validation.images,
            y_: mnist.validation.labels
        }
        evaluate(step, validate_data, validate_writer, "validate")

def evaluate(step, data, writer, name):
    accuracy_val, summary = sess.run([accuracy, summaries], data)
    writer.add_summary(summary, step)
    writer.flush()
    print("Step %i: %s=%f" % (step, name, accuracy_val))

def maybe_save_model(step):
    epoch_step = mnist.train.num_examples / FLAGS.batch_size
    if step != 0 and step % epoch_step == 0:
        save_model()

def save_model():
    print("Saving trained model")
    tf.io.gfile.makedirs(FLAGS.rundir + "/model")
    tf.compat.v1.train.Saver().save(sess, FLAGS.rundir + "/model/export")

def init_test():
    init_session()
    init_exported_collections()
    init_test_writer()

def init_exported_collections():
    global x, y_, accuracy
    saver = tf.train.import_meta_graph(FLAGS.rundir + "/model/export.meta")
    saver.restore(sess, FLAGS.rundir + "/model/export")
    x = tensor_by_collection_name("x")
    y_ = tensor_by_collection_name("y_")
    accuracy = tensor_by_collection_name("acc")

def tensor_by_collection_name(name):
    tensor_name = tf.get_collection(name)[0].decode("UTF-8")
    return sess.graph.get_tensor_by_name(tensor_name)

def init_test_writer():
    global summaries, writer
    summaries = tf.summary.merge_all()
    writer = tf.summary.FileWriter(FLAGS.rundir)

def test():
    data = {x: mnist.test.images, y_: mnist.test.labels}
    test_accuracy, summary = sess.run([accuracy, summaries], data)
    writer.add_summary(summary)
    writer.flush()
    print("Test accuracy=%f" % test_accuracy)

if __name__ == "__main__":
    init_data()
    if FLAGS.just_data:
        pass
    elif FLAGS.test:
        init_test()
        test()
    else:
        init_train()
        train()
