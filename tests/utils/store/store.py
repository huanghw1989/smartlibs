from smart.utils.store.store import *


def test_state():
    store = ContextStore()
    foo = store.state('foo')

    print(foo.name)
    print("set(('a', 'b'), 1)")
    foo.set(('a', 'b'), 1)

    print("\nget('a'): ", foo.get('a'))
    print("\nget(('a', 'b'), 2): ", foo.get(('a', 'b'), 2))

    print("\nget_or_set(('a', 'b'), 2): ", foo.get_or_set(('a', 'b'), 2))
    print("\nget_or_set(('a', 'd'), 3): ", foo.get_or_set(('a', 'd'), 3))
    print('\nget a.d: ', foo.get(('a', 'd')))

    print("\nfoo.delete(('a', 'b')")
    foo.delete(('a', 'b'))
    print('\na(after del): ', foo.get('a'))

    bar = store.state('bar')
    print('all state:', store.get_names('state'))


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)