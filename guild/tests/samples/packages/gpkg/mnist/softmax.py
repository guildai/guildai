import argparse
import json

import tensorflow as tf

from tensorflow.examples.tutorials.mnist import input_data

def init_flags():
    global FLAGS
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="/tmp/MNIST_data",)
    parser.add_argument("--run-dir", default="/tmp/MNIST_train")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--prepare", dest='just_data', action="store_true")
    parser.add_argument("--test", action="store_true")
    FLAGS, _ = parser.parse_known_args()

def init_data():
    global mnist
    mnist = input_data.read_data_sets(FLAGS.data_dir, one_hot=True)

def init_train():
    init_model()
    init_train_op()
    init_eval_op()
    init_summaries()
    init_collections()
    init_session()

def init_model():
    global x, y, W, b
    x = tf.placeholder(tf.float32, [None, 784])
    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))
    y = tf.nn.softmax(tf.matmul(x, W) + b)

def init_train_op():
    global y_, loss, train_op
    y_ = tf.placeholder(tf.float32, [None, 10])
    loss = tf.reduce_mean(
             -tf.reduce_sum(
               y_ * tf.log(y),
               reduction_indices=[1]))
    train_op = tf.train.GradientDescentOptimizer(0.5).minimize(loss)

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
    tf.summary.image("inputs", tf.reshape(x, [-1, 28, 28, 1]), 10)

def init_variable_summaries(var, name):
    with tf.name_scope(name):
        mean = tf.reduce_mean(var)
        tf.summary.scalar("mean", mean)
        stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.summary.scalar("stddev", stddev)
        tf.summary.scalar("max", tf.reduce_max(var))
        tf.summary.scalar("min", tf.reduce_min(var))
        tf.summary.histogram(name, var)

def init_op_summaries():
    tf.summary.scalar("loss", loss)
    tf.summary.scalar("accuracy", accuracy)

def init_summary_writers():
    global summaries, train_writer, validate_writer
    summaries = tf.summary.merge_all()
    train_writer = tf.summary.FileWriter(
        FLAGS.run_dir + "/train",
        tf.get_default_graph())
    validate_writer = tf.summary.FileWriter(
        FLAGS.run_dir + "/validate")

def init_collections():
    tf.add_to_collection("inputs", json.dumps({"image": x.name}))
    tf.add_to_collection("outputs", json.dumps({"prediction": y.name}))
    tf.add_to_collection("x", x.name)
    tf.add_to_collection("y_", y_.name)
    tf.add_to_collection("accuracy", accuracy.name)

def init_session():
    global sess
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

def train():
    steps = (mnist.train.num_examples // FLAGS.batch_size) * FLAGS.epochs
    for step in range(steps):
        images, labels = mnist.train.next_batch(FLAGS.batch_size)
        batch = {x: images, y_: labels}
        sess.run(train_op, batch)
        maybe_log_accuracy(step, batch)
        maybe_save_model(step)

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
    print("Step %i: %s=%f" % (step, name, accuracy_val))

def maybe_save_model(step):
    epoch_step = mnist.train.num_examples / FLAGS.batch_size
    if step != 0 and step % epoch_step == 0:
        save_model()

def save_model():
    print("Saving trained model")
    tf.gfile.MakeDirs(FLAGS.run_dir + "/model")
    tf.train.Saver().save(sess, FLAGS.run_dir + "/model/export")

def init_test():
    init_session()
    init_exported_collections()

def init_exported_collections():
    global x, y_, accuracy
    saver = tf.train.import_meta_graph(FLAGS.run_dir + "/model/export.meta")
    saver.restore(sess, FLAGS.run_dir + "/model/export")
    x = tensor_by_collection_name("x")
    y_ = tensor_by_collection_name("y_")
    accuracy = tensor_by_collection_name("accuracy")

def tensor_by_collection_name(name):
    tensor_name = tf.get_collection(name)[0].decode("UTF-8")
    return sess.graph.get_tensor_by_name(tensor_name)

def test():
    data = {x: mnist.test.images, y_: mnist.test.labels}
    test_accuracy = sess.run(accuracy, data)
    print("Test accuracy=%f" % test_accuracy)

if __name__ == "__main__":
    init_flags()
    init_data()
    if FLAGS.just_data:
        pass
    elif FLAGS.test:
        init_test()
        test()
    else:
        init_train()
        train()
