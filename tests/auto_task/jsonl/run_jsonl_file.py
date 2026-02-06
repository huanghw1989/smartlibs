from smart.auto.run import auto_run


TEST_JSONL_FILE = 'logs/test_jsonl_file.jsonl'


def test_write(file_name=None, file_path=None, root_dir=None):
    """Test Write Jsonl File
    
    Keyword Arguments:
        file_name {str} -- jsonl文件名 (default: {None})
        file_path {str} -- jsonl文件路径 (default: {None})
        root_dir {str} -- 工作根目录 (default: {None})
    """
    file_name = file_name or TEST_JSONL_FILE
    auto_run(
        'auto_tasks.tasks',
        name='task:tools__tool.range~@jsonl__file.write(test_jsonl)',
        extra={
            'configs': {
                'test_jsonl': {
                    'file_name': file_name,
                    'file_path': file_path,
                    'root_dir': root_dir
                }
            }
        } )

def test_read(file_name=None, file_path=None, root_dir=None, head=None):
    """Test Read Jsonl File
    
    Keyword Arguments:
        file_name {str} -- jsonl文件名 (default: {None})
        file_path {str} -- jsonl文件路径 (default: {None})
        root_dir {str} -- 工作根目录 (default: {None})
        head {int} -- None 表示打印所有数据 (default: {None})
    """
    file_name = file_name or TEST_JSONL_FILE
    auto_run(
        'auto_tasks.tasks',
        name='task:jsonl__file.read(test_jsonl)~@tools__print.item_iter',
        bind_arg={
            'tools__print.item_iter': {
                'head': head
            },
        }, 
        extra={
            'configs': {
                'test_jsonl': {
                    'file_name': file_name,
                    'file_path': file_path,
                    'root_dir': root_dir
                }
            }
        } )


if __name__ == "__main__":
    import fire
    
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })