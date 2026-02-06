# 对合成数据集进行分析
# python -m tests.evals.core.data_analysis read_jsonl --offset=0
# python -m tests.evals.core.data_analysis read_jsonl --obj_file 'conclusion_classify/c_predict_result.jsonl' --offset=0
# python -m tests.evals.core.data_analysis read_json
# python -m tests.evals.core.data_analysis predict_result --file_pattern 'c_{}'
# python -m tests.evals.core.data_analysis show_result
# python -m tests.evals.core.data_analysis show_diff
import os, json, pprint, random
import numpy as np
from smart.utils.storage.obj_factory import ObjStorageFactory
from tests.evals import logger
from smart.utils.path import path_join
from smart.utils.dict import dict_safe_set
from smart.utils.jsonl import JsonlReader, JsonlOffsetReader

from tests.configs import smart_env
from smart.evals.core import ItemList, FilterOp, AggregateView, ItemMatrix, MultiLabelMatcher


_store_name = 'local_dataset'
_predict_result_file = 'conclusion_classify/c_f_predict_result_of_gpt_data.jsonl'
_model_meta_file = 'conclusion_classify/c_f_corpus_meta_of_gpt_data.json'


def _get_storage_factory():
    return ObjStorageFactory(
        env=smart_env
    )


def test_read_json(obj_file=None):
    obj_file = obj_file or _model_meta_file
    logger.debug('test_read_json obj_file: %s', obj_file)
    store = _get_storage_factory().get_store_by_env(_store_name)
    cache_file_path = store.fget(obj_file)
    with open(cache_file_path, 'r', encoding='utf8') as fp:
        data = json.load(fp)
        logger.info('data: %s', pprint.pformat(data))


def test_read_jsonl(obj_file=None, size:int=2, offset:int=0):
    obj_file = obj_file or _predict_result_file
    logger.debug('test_read_jsonl obj_file: %s', obj_file)
    store = _get_storage_factory().get_store_by_env(_store_name)
    cache_file_path = store.fget(obj_file)
    with JsonlOffsetReader(cache_file_path) as get_items:
        for item, i in get_items(offset=offset, count=size):
            logger.info('item-%s: %s', i, item)


def test_predict_result(offset:int=0, size:int=2, file_pattern='c_f_{}_of_gpt_data', dir_path='dataset/conclusion_classify'):
    predict_result_file = path_join(dir_path, file_pattern.format('predict_result')+'.jsonl')
    corpus_meta_file = path_join(dir_path, file_pattern.format('corpus_meta')+'.json')

    store = _get_storage_factory().get_store_by_env(_store_name)
    predict_result_local_file = store.fget(predict_result_file)
    corpus_meta_local_file = store.fget(corpus_meta_file)

    corpus_meta_dict = None
    with open(corpus_meta_local_file, 'r', encoding='utf8') as fp:
        corpus_meta_dict = json.load(fp)
    
    labels = corpus_meta_dict['labels']
    label_probs = None
    with JsonlOffsetReader(predict_result_local_file) as get_items:
        for item, i in get_items(offset=offset, count=size):
            label_probs = item.get('label_probs')
            logger.info('item-%s: %s', i, item)
    logger.debug('len(label_probs): %s', len(label_probs or []))
    logger.debug('corpus_meta %s labels: %s', len(labels), labels)


def test_show_result(file_pattern='c_f_{}_of_gpt_data', dir_path='conclusion_classify'):
    store = _get_storage_factory().get_store_by_env(_store_name)

    predict_result_file = path_join(dir_path, file_pattern.format('predict_result')+'.jsonl')
    predict_result_local_file = store.fget(predict_result_file)

    # corpus_meta_file = path_join(dir_path, file_pattern.format('corpus_meta')+'.json')
    # corpus_meta_local_file = store.fget(corpus_meta_file)

    # corpus_meta_dict = None
    # with open(corpus_meta_local_file, 'r', encoding='utf8') as fp:
    #     corpus_meta_dict = json.load(fp)
    
    data = []
    with JsonlReader(predict_result_local_file) as get_items:
        for item in get_items():
            data.append(item)

    op = FilterOp()
    items = ItemList(data=data, id_key='sampleId')
    logger.info('load %s items from: %s', len(items), predict_result_local_file)
    items = items.filter_all([
        # op.startswith('sampleId', 'gpt0601-'),
        # op.list_contain('label_list', "CT 颈椎")
        op._not(op.list_contain('label_list', "CT 颈椎"))
    ])
    logger.info('filter %s items, first: %s', len(items), items[:1])
    all_probs = [
        max(item.get('label_probs') or [0])
        for item in items
    ]
    min_prob, max_prob = min(all_probs), max(all_probs)
    logger.info('min_prob, max_prob=%s, %s', min_prob, max_prob)
    label_group = items.multi_group(
        fn=lambda item: item.get('label_list')
    )
    for label_name, label_items in label_group.items():
        logger.info('label %s has %s items', label_name, len(label_items))

    # 按TP, TN, FP, FN对Items分组
    label_matcher = MultiLabelMatcher()
    eval_group = items.multi_group(
        fn=lambda item: list(label_matcher.measure_group(
            golden=item.get('label_list'),
            pred=item.get('pred_label_list')
        )),
        group_keys=label_matcher.measure_keys()
    )
    measure_counter = {k: len(v) for k, v in eval_group.items()}
    eval_result = label_matcher.calc_metrics_from_counter(measure_counter)
    logger.info('eval_result: %s', eval_result)
    logger.info('measure_counter: %s', measure_counter)

    percentile_list = [0, 25, 50, 75, 100]
    for measure_key, _items in eval_group.items():
        logger.info('measure %s -> %s', measure_key, len(_items))
        for item in _items:
            dict_safe_set(item, ('_eval', measure_key), 1)
        # 分组查看置信度
        all_probs = [
            max(item.get('label_probs') or [0])
            for item in _items
        ]
        aggerate_view = AggregateView()
        aggerate_view.mean().min().max()
        for prob in all_probs:
            aggerate_view.add_value(prob)
        logger.info('prob st: %s', aggerate_view.get_result())

        if len(_items):
            # 置信度分位数
            prob_percentile = np.percentile(all_probs, percentile_list)
            logger.info('prob percentile %s: %s', percentile_list, prob_percentile)
        
        def _boxing_by_prob(item):
            prob = max(item.get('label_probs') or [0])
            group = None
            for i, prob_split in enumerate(prob_percentile[1:]):
                if prob <= prob_split:
                    group = str(percentile_list[i]) + '-' + str(percentile_list[i+1])
                    break
            if group is None: group = str(percentile_list[-1])
            return [group]
        
        prob_boxing_group = _items.multi_group(
            fn=_boxing_by_prob
        )
        prob_group_keys = list(prob_boxing_group.keys())
        # logger.debug('prob_group_keys: %s', prob_group_keys)
        for key in prob_group_keys:
            prob_boxing_items = prob_boxing_group[key]
            for i, item in enumerate(prob_boxing_items[:2]):
                # 每个置信度区间查看2条数据
                prob = max(item.get('label_probs') or [0])
                text = item.get('text')
                label_list = item.get('label_list')
                pred_label_list = item.get('pred_label_list')
                logger.info('# Group=%s, Item-%s, Prob=%s', key, i, prob)
                logger.info('\tText: %s', text)
                logger.info('\tGold: %s', label_list)
                logger.info('\tPred: %s', pred_label_list)

    # 随机抽查一条数据
    rand_idx = random.randint(0, len(items))
    logger.debug('Item-%s: %s', rand_idx, item)

    # 从items的'_eval'字段统计精度指标，跟前面的calc_metrics_from_counter函数是替代关系，计算结果一致
    eval_result2 = label_matcher.calc_metrics_from_items(items=items, item_eval_key='_eval')
    logger.info('eval_result2: %s', eval_result2)
    


def test_show_diff(files=['c_f_{}', 'c_g_{}'], dir_path='conclusion_classify'):
    assert len(files) >= 2

    store = _get_storage_factory().get_store_by_env(_store_name)
    local_file_list = []
    for file_pattern in files:
        predict_file = path_join(dir_path, file_pattern.format('predict_result')+'.jsonl')
        local_file = store.fget(predict_file)
        local_file_list.append(local_file)
    
    all_data = []
    for local_file in local_file_list:
        data = []
        with JsonlReader(local_file) as get_items:
            for item in get_items():
                data.append(item)
            all_data.append(data)
    
    items = ItemList(
        data=all_data[0]
    )
    item_matrix = ItemMatrix.from_list(
        item_list=items,
        column_name=files[0]
    )
    logger.info('item_matrix has %s items', len(item_matrix))

    for idx, item_list in enumerate(all_data[1:]):
        new_column_name = files[idx+1]
        item_matrix.join_items(
            item_list=item_list,
            column_name=new_column_name,
            id_key='sampleId'
        )
    
    intersection_matrix = item_matrix.filter(
        lambda row: all(row) # 所有列都能匹配到的数据
    )
    logger.info('intersection_matrix has %s items', len(intersection_matrix))
    for idx, row in enumerate(intersection_matrix[:2]):
        logger.info('row-%s: %s', idx, row)



if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)