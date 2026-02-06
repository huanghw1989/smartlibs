

class AggregateView:
    def __init__(self, name=None) -> None:
        self._aggregate_fn_dict = {}
        self._display_field = []
        self._state_dict = {}
        self._state2val_dict = {}
        self._name = name

    def add_aggregate_fn(self, name, fn, display:bool=True):
        self._aggregate_fn_dict[name] = fn
        if display and name not in self._display_field:
            self._display_field.append(name)
        return self

    def add_value(self, value):
        for key, fn in self._aggregate_fn_dict.items():
            state = self._state_dict.get(key)
            new_state = fn(state, value)
            self._state_dict[key] = new_state
    
    def update_display_field(self, field, display):
        if display:
            if field not in self._display_field:
                self._display_field.append(field)
        else:
            pop_idx = None
            for idx, value in enumerate(self._display_field):
                if value == field:
                    pop_idx = idx
                    break
            if pop_idx is not None:
                self._display_field.pop(pop_idx)

    def sum(self, display:bool=True):
        def _fn(state, value):
            return (state or 0) + value
        return self.add_aggregate_fn('sum', _fn, display=display)
    
    def count(self, display:bool=True):
        def _fn(state, value):
            return (state or 0) + 1
        return self.add_aggregate_fn('count', _fn, display=display)
    
    def min(self):
        def _fn(state, value):
            return min(state, value) if state is not None else value
        return self.add_aggregate_fn('min', _fn)
    
    def max(self):
        def _fn(state, value):
            return max(state, value) if state is not None else value
        return self.add_aggregate_fn('max', _fn)
    
    def mean(self):
        self.sum(display=False).count(display=False)
        def _get_mean_value(state):
            count_val = self._state_dict.get('count')
            sum_val = self._state_dict.get('sum')
            return sum_val / count_val if count_val else None
        self._state2val_dict['mean'] = _get_mean_value
        self.update_display_field('mean', display=True)
        return self
    
    def get_result(self):
        result_dict = {}
        for field in self._display_field:
            state, value = self._state_dict.get(field), None
            state2val_fn = self._state2val_dict.get(field)
            if state2val_fn:
                value = state2val_fn(state)
            else:
                value = state
            result_dict[field] = value
        return result_dict
