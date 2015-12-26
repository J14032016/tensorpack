#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: example_mnist.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>


# prefer protobuf in user-namespace
import sys
import os
sys.path.insert(0, os.path.expanduser('~/.local/lib/python2.7/site-packages'))

import tensorflow as tf
import numpy as np
from itertools import count


from layers import *
from utils import *
from dataflow.dataset import Mnist
from dataflow import *

IMAGE_SIZE = 28
NUM_CLASS = 10
batch_size = 128
LOG_DIR = 'train_log'

def get_model(input, label):
    """
    Args:
        input: bx28x28
        label: bx1 integer
    Returns:
        (output, cost)
        output: variable
        cost: scalar variable
    """
    # use this dropout variable! it will be set to 1 at test time
    keep_prob = tf.placeholder(tf.float32, shape=tuple(), name='dropout_prob')

    input = tf.reshape(input, [-1, IMAGE_SIZE, IMAGE_SIZE, 1])
    conv0 = Conv2D('conv0', input, out_channel=32, kernel_shape=5,
                  padding='valid')
    conv0 = tf.nn.relu(conv0)
    pool0 = tf.nn.max_pool(conv0, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1],
                           padding='SAME')
    conv1 = Conv2D('conv1', pool0, out_channel=40, kernel_shape=3,
                  padding='valid')
    conv1 = tf.nn.relu(conv1)
    pool1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1],
                           padding='SAME')

    feature = batch_flatten(pool1)

    fc0 = FullyConnected('fc0', feature, 1024)
    fc0 = tf.nn.relu(fc0)
    fc0 = tf.nn.dropout(fc0, keep_prob)

    fc1 = FullyConnected('lr', fc0, out_dim=10)
    prob = tf.nn.softmax(fc1, name='output')

    y = one_hot(label, NUM_CLASS)
    cost = tf.nn.softmax_cross_entropy_with_logits(fc1, y)
    cost = tf.reduce_mean(cost, name='cost')

    tf.scalar_summary(cost.op.name, cost)
    return prob, cost

def main():
    dataset_train = BatchData(Mnist('train'), batch_size)
    dataset_test = BatchData(Mnist('test'), batch_size, remainder=True)
    extensions = [
        OnehotClassificationValidation(
            dataset_test,
            prefix='test', period=2),
        PeriodicSaver(LOG_DIR, period=2)
    ]
    optimizer = tf.train.AdamOptimizer(1e-4)
    sess_config = tf.ConfigProto()
    sess_config.device_count['GPU'] = 1

    with tf.Graph().as_default():
        G = tf.get_default_graph()
        input_var = tf.placeholder(tf.float32, shape=(None, IMAGE_SIZE, IMAGE_SIZE), name='input')
        label_var = tf.placeholder(tf.int32, shape=(None,), name='label')
        prob, cost = get_model(input_var, label_var)

        train_op = optimizer.minimize(cost)

        for ext in extensions:
            ext.init()

        summary_op = tf.merge_all_summaries()
        sess = tf.Session(config=sess_config)
        sess.run(tf.initialize_all_variables())
        summary_writer = tf.train.SummaryWriter(LOG_DIR, graph_def=sess.graph_def)

        keep_prob = G.get_tensor_by_name('dropout_prob:0')
        with sess.as_default():
            for epoch in count(1):
                running_cost = StatCounter()
                for (img, label) in dataset_train.get_data():
                    feed = {input_var: img,
                            label_var: label,
                            keep_prob: 0.5}

                    _, cost_value = sess.run([train_op, cost], feed_dict=feed)
                    running_cost.feed(cost_value)

                print('Epoch %d: avg cost = %.2f' % (epoch, running_cost.average))
                summary_str = summary_op.eval(feed_dict=feed)
                summary_writer.add_summary(summary_str, epoch)

                for ext in extensions:
                    ext.trigger()



if __name__ == '__main__':
    main()
