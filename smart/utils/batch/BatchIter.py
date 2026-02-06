

class BatchItemIter:
    def __init__(self, item_iter, batch_size):
        self._item_iter = item_iter
        self.batch_size = batch_size

    def iter_fn(self):
        if self.batch_size < 2:
            for item in self._item_iter:
                yield [item]
            return

        batch_item = []
        for i, item in enumerate(self._item_iter):
            batch_item.append(item)
            if (i+1) % self.batch_size == 0:
                yield batch_item
                batch_item = []
                
        if len(batch_item):
            yield batch_item
