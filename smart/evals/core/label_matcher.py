from collections import Counter
from smart.utils.dict import dict_find


class BaseLabelMatcher:
    def __init__(self) -> None:
        self._is_negative_label_fn = self._default_negative_label_fn
        self._compare_fn = self._default_compare_fn
        self._format_label_fn = None

    def is_negative_label(self, label):
        return self._is_negative_label_fn(label)
    
    def _default_negative_label_fn(self, label):
        return not label
    
    def set_negative_label_fn(self, fn:callable):
        self._is_negative_label_fn = fn
        return self
    
    def compare_fn(self, golden, pred):
        """比较预测值pred是否与答案golden相同；比较前会先用format_labels函数统一格式

        Args:
            golden (any): 答案
            pred (any): 预测值

        Returns:
            bool: True代表相同, False代表不同
        """
        _formated_golden = self.format_label(golden)
        _formated_pred = self.format_label(pred)
        return self._compare_fn(_formated_golden, _formated_pred)
    
    def _default_compare_fn(self, golden, pred):
        return golden == pred

    def set_compare_fn(self, fn:callable):
        self._compare_fn = fn
        return self
  
    def format_label(self, label):
        if self._format_label_fn is not None:
            return self._format_label_fn(label)
        return label
    
    def set_format_label_fn(self, fn:callable):
        self._format_label_fn = fn
        return self
    
    def calc_metrics_from_counter(self, counter:dict, num_items:int=None):
        """从counter计算指标

        Args:
            counter (dict|Counter): {'TP': 数量, 'TN': 数量, 'FP': 数量, 'FN': 数量}
        """
        TP = counter.get('TP') or 0
        TN = counter.get('TN') or 0
        FP = counter.get('FP') or 0
        FN = counter.get('FN') or 0
        
        if num_items is None:
            num_items = TP + TN + FP + FN
        
        if not num_items:
            return {}
        
        accuracy = (TP + TN) / num_items
        precision = TP / max(TP + FP, 1)
        recall = TP / max(TP + FN, 1)
        f1 = 2 * TP / max(2 * TP + FP + FN, 1)

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    def calc_metrics_from_items(self, items:list, item_eval_key:str='_eval'):
        counter = Counter()
        for item in items:
            item_eval = dict_find(item, item_eval_key) or {}
            for key, val in item_eval.items():
                if val:
                    counter[key] += 1
        return self.calc_metrics_from_counter(counter, num_items=len(items))


class MultiLabelMatcher(BaseLabelMatcher):
    def __init__(self) -> None:
        super().__init__()
        self._format_label_fn = self.sorted_labels

    def _default_negative_label_fn(self, labels):
        return not len(labels)
    
    def sorted_labels(self, lable_list):
        return sorted(lable_list)
    
    def measure_keys(self):
        return ('TP', 'TN', 'FP', 'FN')

    def measure_group(self, golden, pred):
        golden_is_negative = self.is_negative_label(golden)
        pred_is_negative = self.is_negative_label(pred)
        if pred_is_negative:
            if golden_is_negative:
                # 真负例
                yield 'TN'
            else:
                # 假负例
                yield 'FN'
        else:
            is_same = self.compare_fn(golden, pred)
            if is_same:
                # 真正例
                yield 'TP'
            else:
                # 假正例
                yield 'FP'