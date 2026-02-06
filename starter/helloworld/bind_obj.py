"""Ch3. Bind Arg For Task Method

Command: python -m smart.auto.run starter.helloworld.auto learn_bind_obj
"""
import random

from .utils import lazy, auto_load


def linear_dataset(size=1000, weight=12.3, bias=-11.1, noise=.1):
    tf = lazy.tf
    print('linear_dataset', (size, weight, bias, noise))
    
    def data_gen():
        print('linear_dataset data_gen begin')
        for i in range(size):
            x = round(random.random() * 100, 5)
            y = weight * x + bias
            y *= 1 + random.random() * noise
            y = round(y, 5)
            yield {'x': x, 'y': y}
        print('linear_dataset data_gen end')

    return tf.data.Dataset.from_generator(
        data_gen, 
        {
            'x': tf.float32, 
            'y': tf.float32
        }, 
        {
            'x': tf.TensorShape([]), 
            'y': tf.TensorShape([])
        }
    )


def mse_loss(x, y, w, b):
    tf = lazy.tf
    return tf.reduce_mean(tf.square(x * w + b - y))


@auto_load.func_task('linear_solve')
@auto_load.bind_obj(linear_dataset, 'linear_solve.linear_dataset')
# @auto_load.bind_obj('tensorflow', arg_name='tf')
def linear_solve(task, linear_dataset):
    tf = lazy.tf
    tf.enable_eager_execution()

    ds = linear_dataset()
    ds.shuffle(100)

    batch_size = 16
    epoch = 5
    # train_steps = 1000
    learning_rate = 0.00001

    var_W = tf.Variable(1.0)
    var_B = tf.Variable(0.)
    
    print('# Train By Gradient #')
    for epoch_idx in range(epoch):
        print('\n---epoch', epoch_idx)
        i, loss_sum, count = 0, 0, 0
        for items in ds.batch(batch_size).make_one_shot_iterator():
            x, y = items['x'], items['y']
            with tf.GradientTape() as tape:
                loss = mse_loss(x, y, var_W, var_B)
                dW, dB = tape.gradient(loss, [var_W, var_B])
            var_W.assign_sub(dW * learning_rate)
            var_B.assign_sub(dB * learning_rate)
            loss_sum += loss.numpy()
            count += batch_size
            i += 1
            if i % 100 == 0:
                print("Loss at step {:03d}: {:.3f}".format(i, loss(var_W, var_B)))
        print('w: {}, b: {}'.format(str(var_W.numpy()), str(var_B.numpy())))
        print('mean loss', loss_sum/count)
