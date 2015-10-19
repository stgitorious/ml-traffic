import numpy as np
from abc import ABCMeta, abstractmethod


class AbstractLearner(metaclass=ABCMeta):

    def __init__(self):
        self.classes = []
        self.labels = []

    def train(self, x_train, y_train):
        self._extract_classes(y_train)
        self._train(x_train, self.labels)

    @abstractmethod
    def _train(self, x_train, y_train):
        pass

    def _extract_classes(self, y_train):
        self.classes = list(set(y_train))
        class_to_index = {key: index for index, key in enumerate(self.classes)}
        self.labels = np.concatenate(np.array([[class_to_index[name] for name in y_train]]))

    def predict(self, x):
        indices = self._predict(x)
        return [self.classes[idx] for idx in indices]

    @abstractmethod
    def _predict(self, x):
        pass

    @abstractmethod
    def predict_proba(self, x):
        pass