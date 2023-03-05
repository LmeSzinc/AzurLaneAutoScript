from __future__ import print_function


class CnHyperparams(object):
    """
    Hyperparameters for LSTM network
    """

    def __init__(self):
        # Training hyper parameters
        # self._train_epoch_size = 2560000
        # self._eval_epoch_size = 3000
        self._num_epoch = 20
        self._loss_type = "ctc"
        self.optimizer = "Adam"
        self._learning_rate = 0.001
        self.wd = 0.00001
        self.clip_gradient = None  # `None`: don't use clip gradient
        # self._momentum = 0.9
        # self._bn_mom = 0.9
        # self._workspace = 512

        self._batch_size = 128
        self._num_classes = 6426  # 应该是6426的。。 5990
        self._img_width = 280
        self._img_height = 32

        # LSTM hyper parameters
        self.seq_model_type = "lstm"
        self._num_hidden = 128
        self._num_lstm_layer = 1

        # 模型对于图片宽度压缩的比例（模型中的卷积层造成的）；由模型决定，不同模型不一样
        self.seq_len_cmpr_ratio = None
        # 序列长度；由模型决定，不同模型不一样
        self._seq_length = None
        self._num_label = 20
        self._drop_out = 0.3

    def __repr__(self):
        return str(self.__dict__)

    def set_seq_length(self, seq_len):
        self._seq_length = seq_len

    # @property
    # def train_epoch_size(self):
    #     return self._train_epoch_size
    #
    # @property
    # def eval_epoch_size(self):
    #     return self._eval_epoch_size

    @property
    def num_epoch(self):
        return self._num_epoch

    @property
    def learning_rate(self):
        return self._learning_rate

    @property
    def momentum(self):
        return self._momentum

    # @property
    # def bn_mom(self):
    #     return self._bn_mom
    #
    # @property
    # def workspace(self):
    #     return self._workspace

    @property
    def loss_type(self):
        return self._loss_type

    @property
    def batch_size(self):
        return self._batch_size

    @property
    def num_classes(self):
        return self._num_classes

    @property
    def img_width(self):
        return self._img_width

    @property
    def img_height(self):
        return self._img_height

    @property
    def depth(self):
        return self._depth

    @property
    def growrate(self):
        return self._growrate

    @property
    def reduction(self):
        return self._reduction

    @property
    def num_hidden(self):
        return self._num_hidden

    @property
    def num_lstm_layer(self):
        return self._num_lstm_layer

    @property
    def seq_length(self):
        return self._seq_length

    @property
    def num_label(self):
        return self._num_label

    @property
    def dropout(self):
        return self._drop_out
