from PIL import Image
from torch.utils.data import Dataset
from .data_generator import SimpleRandomWordGenerator


class SyntheticOnlineDataset(Dataset):
    def __init__(self, fonts_dir, size, word_sampler,
                 bg_range=(255, 255),
                 color_range=(0, 100),
                 font_size_range=(50, 100),
                 rotation_range=(0, 0)):
        super().__init__()
        self.size = size
        self.fonts_dir = fonts_dir

        simple_generator = SimpleRandomWordGenerator(word_sampler, self.fonts_dir,
                                                     bg_range=bg_range,
                                                     color_range=color_range,
                                                     font_size_range=font_size_range,
                                                     rotation_range=rotation_range)
        self.iterator = iter(simple_generator)

    def __getitem__(self, idx):
        if 0 <= idx < len(self):
            return self.generate_example()
        else:
            raise IndexError()

    def generate_example(self):
        im, word = next(self.iterator)
        return im, word

    def __len__(self):
        return self.size


class SyntheticOnlineDatasetCached(SyntheticOnlineDataset):
    def __init__(self, fonts_dir, size, word_sampler, bg_range=(255, 255),
                 color_range=(0, 100), font_size_range=(50, 100), rotation_range=(0, 0)):
        super().__init__(fonts_dir, size, word_sampler,
                         bg_range=bg_range,
                         color_range=color_range,
                         font_size_range=font_size_range,
                         rotation_range=rotation_range)

        self.cache = {}

    def __getitem__(self, idx):
        if idx not in self.cache:
            self.cache[idx] = super().__getitem__(idx)

        return self.cache[idx]


class IAMWordsDataset(Dataset):
    def __init__(self, index_path):
        super().__init__()
        self.index_path = index_path
        self.iam_index = []

        self.re_build()

    def re_build(self):
        self.iam_index = []
        with open(self.index_path) as f:
            for line in f:
                path, gray_level, transcript = line.split(',')
                path = path.strip()
                transcript = transcript.strip()
                gray_level = int(gray_level.strip())
                self.iam_index.append((path, gray_level, transcript))

    def __getitem__(self, idx):
        path, gray_level, transcript = self.iam_index[idx]
        image = Image.open(path)
        image = clean_image(image, gray_level)
        return path, gray_level, image, transcript

    def __len__(self):
        return len(self.iam_index)


class UnlabeledDataset(IAMWordsDataset):
    def __getitem__(self, idx):
        path, gray_level, image, transcript = super().__getitem__(idx)
        return path, gray_level, image


class LabeledDataset(IAMWordsDataset):
    def __getitem__(self, idx):
        path, gray_level, image, transcript = super().__getitem__(idx)
        return image, transcript


def clean_image(image, gray_level):
    return image.point(lambda p: 255 if p > gray_level else p)
