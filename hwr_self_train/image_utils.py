from torchvision.transforms import Resize, Pad


def clip_height(images, max_value):
    """Ensure every image has at most max_value height"""
    res = []
    for im in images:
        image = im if im.height <= max_value else fit_height(im, max_value)
        res.append(image)
    return res


def fit_height(image, target_height):
    """Resize image to have target_height height and keep its aspect ratio"""
    w = image.width
    h = image.height

    scaler = target_height / h

    target_width = int(round(scaler * w))

    resizer = Resize((target_height, target_width))
    return resizer(image)


def resize_all(images, height):
    """Resize all images to specified height whilst retaining the aspect ratio"""
    return [fit_height(im, height) for im in images]


def pad_images(images, pad_strategy=None, max_height=None, fill=255):
    pad_strategy = pad_strategy or one_sided_padding

    max_height = max_height or compute_max_height(images)
    max_width = compute_max_width(images)

    max_width = nearest_divisible_by(max_width)

    padded = []
    for im in images:
        padding_top, padding_bottom = pad_strategy(max_height, im.height)
        padding_left, padding_right = pad_strategy(max_width, im.width)

        pad = Pad((padding_left, padding_top, padding_right, padding_bottom),
                  fill=fill)
        padded.append(pad(im))

    return padded


def compute_max_height(images):
    return max([im.height for im in images])


def compute_max_width(images):
    return max([im.width for im in images])


def nearest_divisible_by(value, factor=32):
    """Calculate the smallest integer larger than or equal to the value divisible by factor"""
    if value % factor != 0:
        value = (value // factor + 1) * factor
    return value


def equal_padding(max_length, length):
    len_diff = max_length - length
    padding1 = len_diff // 2
    padding2 = len_diff - padding1
    return padding1, padding2


def one_sided_padding(max_length, length):
    len_diff = max_length - length
    return 0, len_diff


def to_rgb(tensor):
    """Convert tensor with single channel to tensor with 3 channels.

    Simply repeat same channel 3 times

    :param tensor: Corresponding to the image tensor of shape (1, height, width)
    :return: Tensor of shape (3, height, width)
    """
    return tensor.repeat(3, 1, 1)
