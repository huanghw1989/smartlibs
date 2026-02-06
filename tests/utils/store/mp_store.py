import multiprocessing as mp
import time, logging

from smart.utils.store.mp_store import *

logger = logging.getLogger('test')


def mp_fn(i, store, foo:MpState):
    # print('f.g:', f.get('g'))
    # foo2 = store_dict.get((0, 'foo'))
    # foo = store.state('foo')

    def set_fn():
        print('enter set_fn', i)
        time.sleep(1)
        return i
    
    print('get_or_set_fn {} (x.b): '.format(i), foo.get_or_set_fn(('x', 'b'), set_fn))
    print('get_or_set_fn {} again(x.b): '.format(i), foo.get_or_set_fn(('x', 'b'), set_fn))

    for j in range(2):
        print('foo.set_fn(x.counter) {}-{}'.format(i, j), 
            foo.set_fn(('x', 'counter'), lambda x: (x or 0) + 1)
        )

    print('all state', i, store.get_names('state'))
    

def test_state(process_num=None, debug=False):
    store = MpContextStore()

    if debug:
        from smart.utils.remote_debug import enable_remote_debug
        enable_remote_debug()
    
    foo = store.state('foo')

    print(foo.name)
    print("set(('a', 'b'), 1)")
    foo.set(('a', 'b'), 1)

    print('\na: ', foo.get('a'))
    print("\nfoo.get(('a', 'b'), 2): ", foo.get(('a', 'b'), 2))

    print("\nfoo.get_or_set(('a', 'b'), 2): ", foo.get_or_set(('a', 'b'), 2))
    print("\nfoo.get_or_set(('a', 'd', 'e'), 3: ", foo.get_or_set(('a', 'd', 'e'), 3))

    print('\nget a.d:', foo.get(('a', 'd')))
    print('\na:', foo.get('a'))

    f = store._manager.dict()
    print("\n# Nest DictProxy Test")
    foo.set(('a', 'f'), f)

    print('\nf: ', f)
    print("\nfoo.get_or_set(('a', 'f', 'g'), xxx: ", foo.get_or_set(('a', 'f', 'g'), 'xxx'))
    print('\nf: ', f)

    print("\nfoo.delete(('a', 'b'))")
    foo.delete(('a', 'b'))
    print('\na(after del): ', foo.get('a'))

    store_dict = store.store_dict

    bar = store.state('bar')
    
    print('\n# mp Test-->')
    if process_num:
        process_list = []

        for i in range(process_num):
            process = mp.Process(target=mp_fn, args=(i, store, foo))
            process.start()
            process_list.append(process)
            print('start process', process.pid)
        
        store.state('key_after_process')

        for process in process_list:
            process.join()
    else:
        mp_fn(0, store, foo)
    
    print('\n# Readonly Test-->')
    print('bar.get_or_set: ', 
        bar.get_or_set(('a', 'b'), 1))
    print('bar set_readonly')
    bar.set_readonly()
    print('bar.set:', bar.set(('a', 'b'), 2))
    print('bar.get:', bar.get(('a', 'b')))
    print('bar.get_or_set:', bar.get_or_set(('a', 'b'), 3))
    print('bar.get_or_set a.c:', bar.get_or_set(('a', 'c'), 1))
    print('bar.get a.c:', bar.get(('a', 'c')))
    

def test_list():
    store = MpContextStore()
    l = store.list('foo')
    l.append(1)
    print('l:', list(l))
    l.extend([2, 3])
    print('l:', list(l))
    print('l.pop:', l.pop())
    print('l:', list(l))


def test_dict():
    store = MpContextStore()
    d = store.dict('foo')
    print('d: ', dict(d))
    d.update({
        'a': {
            'b': 1
        }
    })
    print('d: ', dict(d))
    del d['a']
    print('d(after del): ', dict(d))


def test_value(debug=False):
    store = MpContextStore()

    if debug:
        from smart.utils.remote_debug import enable_remote_debug
        enable_remote_debug()
    
    foo = store.value('foo')

    assert foo.__hash__ == store.value('foo').__hash__

    print('get foo:', foo.get('no value'))
    foo.set('bar')
    print("foo.set('bar')")
    print('get foo:', foo.get('no value'))
    foo.delete()
    print("foo.delete()")
    print('get foo:', foo.get('no value'))

def _test_state_wait(store, key_path, timeout, *args):
    # state = store.state('test_state_wait')
    val = store.state('test_state_wait').wait(key_path, timeout=timeout)
    logger.info('test_state_wait sewaitt: %s', val)

def test_state_wait(delay=1.1, timeout=5):
    store = MpContextStore()
    # 事先创建state, 避免spawn多进程下被回收
    state = store.state('test_state_wait')

    key_path = ('a', 'b')

    process = mp.Process(target=_test_state_wait, args=(store, key_path, timeout))
    process.start()

    time.sleep(delay)

    # state = store.state('test_state_wait')

    val = time.time()
    store.state('test_state_wait').set(key_path, val)
    logger.info('test_state_wait set: %s', val)

    process.join()
    store.state('test_state_wait').set(key_path, 222)


if __name__ == "__main__":
    mp.set_start_method('spawn', True)

    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)