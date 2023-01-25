import torch
from torch.optim import Adam
from torchmetrics import CharErrorRate

from hwr_self_train.preprocessors import CharacterTokenizer, decode_output_batch
from hwr_self_train.loss_functions import MaskedCrossEntropy
from hwr_self_train.loss_functions import LossTargetTransform
from hwr_self_train.metrics import Metric
from hwr_self_train.training import get_simple_trainer, get_consistency_trainer
from hwr_self_train.word_samplers import UniformSampler, FrequencyBasedSampler

tokenizer = CharacterTokenizer()


def decode(y_hat, y):
    y_hat = decode_output_batch(y_hat, tokenizer)
    return y_hat, y


loss_conf = {
    'class': MaskedCrossEntropy,
    'kwargs': dict(reduction='sum', label_smoothing=0.6),
    'transform': LossTargetTransform(tokenizer)
}


cer_conf = {
    'class': CharErrorRate,
    'transform': decode
}


optimizer_conf = {
    'class': Adam,
    'kwargs': dict(lr=0.0001)
}


class Configuration:
    image_height = 64
    hidden_size = 128

    iam_pseudo_labels = 'iam/pseudo_labels.txt'
    iam_train_path = 'iam/iam_train.txt'
    iam_dataset_path = 'iam/iam_val.txt'
    confidence_threshold = 0.4

    fonts_dir = './fonts'

    word_sampler = FrequencyBasedSampler.from_file("word_frequencies.csv")

    training_set_size = 50000
    validation_set_size = 2500

    batch_size = 32
    num_workers = 2

    loss_function = loss_conf

    encoder_optimizer = optimizer_conf
    decoder_optimizer = optimizer_conf

    training_metrics = {
        'loss': loss_conf,
        'CER': cer_conf
    }

    # evaluated using the same augmentation used in training dataset
    train_val_metrics = {
        'train-val loss': loss_conf,
        'train-val CER': cer_conf
    }

    # evaluated without using augmentation
    validation_metrics = {
        'val loss': loss_conf,
        'val CER': cer_conf
    }

    # evaluated on IAM dataset (without augmentation)
    test_metrics = {
        'iam loss': loss_conf,
        'iam CER': cer_conf
    }

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    checkpoints_save_dir = 'checkpoints'
    tuning_checkpoints_dir = 'tuning_checkpoints'

    history_path = 'pretrain_history.csv'
    tuning_history_path = 'tuning_history.csv'

    evaluation_steps = {
        'training_set': 0.1,
        'train_validation_set': 1.0,
        'validation_set': 1.0,
        'test_set': 0.5
    }
    epochs = 5
    tuning_epochs = 50

    tuning_trainer_factory = get_simple_trainer
    weak_augment_options = dict(
        p_augment=0.4,
        target_height=64,
        fill=255,
        rotation_degrees_range=(-5, 5),
        blur_size=3,
        blur_sigma=[1, 1],
        noise_sigma=10,
        should_fit_height=False
    )


def create_metric(name, metric_fn, transform_fn):
    return Metric(
        name, metric_fn=metric_fn, metric_args=["y_hat", "y"], transform_fn=transform_fn
    )


def create_optimizer(model, optimizer_conf):
    optimizer_class = optimizer_conf['class']
    kwargs = optimizer_conf['kwargs']
    return optimizer_class(model.parameters(), **kwargs)


def prepare_loss(loss_conf):
    loss_class = loss_conf["class"]
    loss_kwargs = loss_conf["kwargs"]
    loss_transform = loss_conf["transform"]
    loss_function = loss_class(**loss_kwargs)
    return create_metric('loss', loss_function, loss_transform)


def prepare_metrics(metrics_conf):
    metric_fns = {}
    for name, spec in metrics_conf.items():
        metric_class = spec['class']
        metric_args = spec.get('args', [])
        metric_kwargs = spec.get('kwargs', {})
        transform_fn = spec['transform']
        metric_fn = metric_class(*metric_args, **metric_kwargs)

        metric_fns[name] = create_metric(name, metric_fn, transform_fn)

    return metric_fns
