from smart.rest.util.url_path import *

def test_url_path_match():
    to_match_path_pairs = [
        # (to_match_path, pattern_path, expect)
        ('/', None, True),
        ('/', '/', True),
        ('/a/b', '/**', True),
        ('/a/b', '/*', False),
        ('a/b', '*/{p1}', {'p1':'b'}),
        ('a/b/c', '**/{p1}/{p2}', {'p1':'b', 'p2':'c'}),
        ('aaa', '**/{p1}/{p2}', False),
    ]

    for to_match_path, pattern_path, expect in to_match_path_pairs:
        to_match_pathes = tuple(filter(None, to_match_path.split('/')))
        pattern_pathes = pattern_path if pattern_path is None else tuple(filter(None, pattern_path.split('/')))
        match_rst = url_path_match(to_match_pathes, pattern_pathes)
        print(to_match_path, pattern_path, to_match_pathes, pattern_pathes, match_rst)
        assert match_rst == expect


if __name__ == "__main__":
    import fire
    
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })