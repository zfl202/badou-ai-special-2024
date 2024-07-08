import tensorflow as tfslim = tf.contrib.slimimport readcifar10import osdef model_fn_v1(net,keep_prob=0.5, is_training = True):    batch_norm_params = {    'is_training': is_training,    'decay': 0.997,    'epsilon': 1e-5,    'scale': True,    'updates_collections': tf.GraphKeys.UPDATE_OPS,    }    endpoints = {}    with slim.arg_scope(            [slim.conv2d],            weights_regularizer=slim.l2_regularizer(0.0001),            weights_initializer=slim.variance_scaling_initializer(),            activation_fn=tf.nn.relu,            normalizer_fn=slim.batch_norm,            normalizer_params=batch_norm_params):        with slim.arg_scope([slim.batch_norm], **batch_norm_params):            with slim.arg_scope([slim.max_pool2d], padding='SAME') as arg_sc:                net = slim.conv2d(net, 32, [3, 3], activation_fn=None, normalizer_fn=None, scope='conv1')                net = slim.conv2d(net, 32, [3, 3], activation_fn=None, normalizer_fn=None, scope='conv2')                endpoints["conv2"] = net                net = slim.max_pool2d(net, [3, 3], stride=2, scope="pool1")                net = slim.conv2d(net, 64, [3, 3], activation_fn=None, normalizer_fn=None, scope='conv3')                net = slim.conv2d(net, 64, [3, 3], activation_fn=None, normalizer_fn=None, scope='conv4')                endpoints["conv4"] = net                net = slim.max_pool2d(net, [3, 3], stride=2, scope="pool2")                net = slim.conv2d(net, 128, [3, 3], activation_fn=None, normalizer_fn=None, scope='conv5')                net = slim.conv2d(net, 128, [3, 3], activation_fn=None, normalizer_fn=None, scope='conv6')                net = tf.reduce_mean(net, [1, 2], name='pool5', keep_dims=True)                net = slim.flatten(net)                net = slim.dropout(net, keep_prob, scope='dropout1')                net = slim.fully_connected(net, 10, activation_fn=None, scope='fc2')                endpoints["fc"] = net    return netdef resnet_blockneck(net, kernel_size, down, stride, is_training):    batch_norm_params = {    'is_training': is_training,    'decay': 0.997,    'epsilon': 1e-5,    'scale': True,    'updates_collections': tf.GraphKeys.UPDATE_OPS,    }    shortcut = net    with slim.arg_scope(                [slim.conv2d],                weights_regularizer=slim.l2_regularizer(0.0001),                weights_initializer=slim.variance_scaling_initializer(),                activation_fn=tf.nn.relu,                normalizer_fn=slim.batch_norm,                normalizer_params=batch_norm_params):        with slim.arg_scope([slim.batch_norm], **batch_norm_params):            with slim.arg_scope([slim.conv2d, slim.max_pool2d], padding='SAME') as arg_sc:                if kernel_size != net.get_shape().as_list()[-1]:                    shortcut = slim.conv2d(net, kernel_size, [1, 1])                if stride != 1:                    shortcut = slim.max_pool2d(shortcut, [3, 3], stride=stride, scope="pool1")                net = slim.conv2d(net, kernel_size // down, [1, 1])                net = slim.conv2d(net, kernel_size // down, [3, 3])                if stride != 1:                    net = slim.max_pool2d(net, [3, 3], stride=stride, scope="pool1")                net = slim.conv2d(net, kernel_size, [1, 1])    net =  net + shortcut    return netdef model_fn_resnet(net, keep_prob=0.5, is_training = True):    with slim.arg_scope([slim.conv2d, slim.max_pool2d], padding='SAME') as arg_sc:        net = slim.conv2d(net, 64, [3, 3], activation_fn=tf.nn.relu)        net = slim.conv2d(net, 64, [3, 3], activation_fn=tf.nn.relu)        net = resnet_blockneck(net, 128, 4, 2, is_training)        net = resnet_blockneck(net, 128, 4, 1, is_training)        net = resnet_blockneck(net, 256, 4, 2, is_training)        net = resnet_blockneck(net, 256, 4, 1, is_training)        net = resnet_blockneck(net, 512, 4, 2, is_training)        net = resnet_blockneck(net, 512, 4, 1, is_training)        #net = tf.reduce_mean(net, [1, 2], name='pool5', keep_dims=True)        net = slim.flatten(net)        net = slim.fully_connected(net, 1024, activation_fn=tf.nn.relu, scope='fc1')        net = slim.dropout(net, keep_prob, scope='dropout1')        net = slim.fully_connected(net, 10, activation_fn=None, scope='fc2')    return netdef model(image, keep_prob=0.5, is_training=True):    batch_norm_params = {        "is_training": is_training,        "epsilon": 1e-5,        "decay": 0.997,        'scale': True,        'updates_collections': tf.GraphKeys.UPDATE_OPS    }    with slim.arg_scope(            [slim.conv2d],            weights_initializer=slim.variance_scaling_initializer(),            activation_fn=tf.nn.relu,            weights_regularizer=slim.l2_regularizer(0.0001),            normalizer_fn=slim.batch_norm,            normalizer_params=batch_norm_params):        net = slim.conv2d(image, 32, [3, 3], scope='conv1')        net = slim.conv2d(net, 32, [3, 3], scope='conv2')        net = slim.max_pool2d(net, [3, 3], stride=2, scope='pool1')        net = slim.conv2d(net, 64, [3, 3], scope='conv3')        net = slim.conv2d(net, 64, [3, 3], scope='conv4')        net = slim.max_pool2d(net, [3, 3], stride=2, scope='pool2')        net = slim.conv2d(net, 128, [3, 3], scope='conv5')        net = slim.conv2d(net, 128, [3, 3], scope='conv6')        net = slim.max_pool2d(net, [3, 3], stride=2, scope='pool3')        net = slim.conv2d(net, 256, [3, 3], scope='conv7')        net = tf.reduce_mean(net, axis=[1, 2])  # nhwc--n11c        net = slim.flatten(net)        net = slim.fully_connected(net, 1024)        net = slim.dropout(net, keep_prob)        net = slim.fully_connected(net, 10)    return net  # 10 dim vecdef func_optimal(loss_val):    with tf.variable_scope("optimizer"):        global_step = tf.Variable(0, trainable=False)        lr = tf.train.exponential_decay(0.0001, global_step,                                                   decay_steps=10000,                                                   decay_rate=0.99,                                                   staircase=True)        # ##更新 BN        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)        with tf.control_dependencies(update_ops):            optimizer = tf.train.AdamOptimizer(lr).minimize(loss_val, global_step)        return optimizer, global_step, lrdef loss(logist, label):    one_hot_label = slim.one_hot_encoding(label, 10)    slim.losses.softmax_cross_entropy(logist, one_hot_label)    reg_set = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)    l2_loss = tf.add_n(reg_set)    slim.losses.add_loss(l2_loss)    totalloss = slim.losses.get_total_loss()    return totalloss, l2_lossdef train_net():    batchsize = 128    floder_name = "logdirs"    no_data = 1    if not os.path.exists(floder_name):        os.mkdir(floder_name)    images_train, labels_train = readcifar10.read_from_tfrecord_v1(batchsize, 0, no_data)    images_test, labels_test = readcifar10.read_from_tfrecord_v1(batchsize, 1)    input_data  = tf.placeholder(tf.float32, shape=[None, 32, 32, 3], name="input_224")    input_label = tf.placeholder(tf.int64, shape=[None], name="input_label")    is_training = tf.placeholder(tf.bool, shape=None, name = "is_training")    keep_prob   = tf.placeholder(tf.float32, shape=None, name= "keep_prob")    logits      = model(input_data, keep_prob=keep_prob)    softmax     = tf.nn.softmax(logits)    pred_max        = tf.argmax(softmax, 1)    correct_pred    = tf.equal(input_label, pred_max)    accurancy       = tf.reduce_mean(tf.cast(correct_pred, tf.float32))    total_loss, l2_loss = loss(logits, input_label)    # one_hot_labels = slim.one_hot_encoding(input_label, 10)    # slim.losses.softmax_cross_entropy(logits, one_hot_labels)    #    # reg_set = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)    # l2_loss = tf.add_n(reg_set)    # slim.losses.add_loss(l2_loss)    # total_loss      = slim.losses.get_total_loss()    #如果使用了自己定义的loss，而又想使用slim的loss管理机制，可以使用：    # Build a Graph that trains the model with one batch of examples and    # updates the model parameters.    update_op, global_step, learning_rate = func_optimal(total_loss)    summaries_train = set()    summaries_test = set()    # summaries.add(tf.summary.image("train image", tf.cast(images_train, tf.uint8)))    summaries_train.add(tf.summary.scalar('train_total_loss', total_loss))    summaries_train.add(tf.summary.scalar('train_l2_loss', l2_loss))    summaries_test.add(tf.summary.scalar('test_total_loss', total_loss))    summaries_train.add(tf.summary.scalar('learning rate', learning_rate))    summaries_train.add(tf.summary.image("image_train", images_train *128 + 128))    summaries_test.add(tf.summary.image("image_test", images_test * 128 + 128))    sess_config = tf.ConfigProto()    sess_config.gpu_options.allow_growth = True    with tf.Session(config=sess_config) as sess:        sess.run(tf.local_variables_initializer())        sess.run(tf.global_variables_initializer())        coord = tf.train.Coordinator()        tf.train.start_queue_runners(sess=sess, coord=coord)        init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())        sess.run(init_op)        saver = tf.train.Saver(tf.global_variables(), max_to_keep=5)        ckpt = tf.train.latest_checkpoint(floder_name)        summary_writer = tf.summary.FileWriter(floder_name, sess.graph)        summary_train_op = tf.summary.merge(list(summaries_train))        summary_test_op = tf.summary.merge(list(summaries_test))        #        #        if ckpt:           print("Model restored...",ckpt)           saver.restore(sess, ckpt)        for itr in range(1000000):            train_images, train_label = sess.run([images_train, labels_train])            train_feed_dict = {input_data: train_images,                               input_label: train_label,                               is_training: True, keep_prob: 1.0}            _, global_step_val ,accurancy_val, learning_rate_val, loss_val, pred_max_val, summary_str = \                sess.run([update_op, global_step,  accurancy, learning_rate, total_loss, pred_max, summary_train_op], feed_dict=train_feed_dict)            summary_writer.add_summary(summary_str, global_step_val)            if itr % 100 == 0:                print("itr:{}, train acc: {},total_loss: {},   lr: {}".format(itr, accurancy_val,loss_val, learning_rate_val))                test_images, test_label = sess.run([images_test, labels_test])                test_feed_dict = {input_data: test_images,                                   input_label: test_label,                                   is_training: False,                                   keep_prob: 1.0}                accurancy_val, pred_max_val, summary_str = \                    sess.run([accurancy, pred_max, summary_test_op],                             feed_dict=test_feed_dict)                summary_writer.add_summary(summary_str, global_step_val)                print("itr:{}, test acc: {},  lr: {}".format(itr,accurancy_val,                                                                        learning_rate_val))                print(test_label)                print(pred_max_val)            if itr % 100 == 0:                saver.save(sess, "{}/model.ckpt".format(floder_name) + str(global_step_val), global_step=1)if __name__ == '__main__':    print("begin..")    train_net()