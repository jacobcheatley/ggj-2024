from pathlib import Path

import numpy as np
from PIL import Image

PALETTE_BASE_COLORS = [(255, 255, 0), (0, 0, 255)]

PALETTE_AVAILABLE_COLORS = [
    (230, 230, 230),
    (103, 96, 79),
    (203, 47, 52),
    (246, 140, 30),
    (229, 213, 31),
    (117, 172, 72),
    (61, 163, 151),
    (95, 134, 201),
    (83, 73, 125),
    (211, 89, 185),
]


IMAGE_DIR = Path("jest_fest/static/images")
SOURCE_DIRS = ["jesters"]
DEST_DIR = Path("jest_fest/static/images/palettes")


class FrameGetter:
    def __init__(self) -> None:
        self.d = {}
        self._layer_count = 1
        self._frame_count = 1

    def add_frame(self, fn: Path, layer: int, frame: int | None = None):
        if frame is None:
            self.d[layer] = fn
        else:
            self.d[(layer, frame)] = fn
            self._frame_count = max(self._frame_count, frame + 1)
        self._layer_count = max(self._layer_count, layer + 1)

    def _get(self, layer, frame):
        if (layer, frame) in self.d:
            return self.d[(layer, frame)]
        else:
            return self.d[layer]

    def iterate(self):
        for frame_index in range(self._frame_count):
            yield [self._get(layer_index, frame_index) for layer_index in range(self._layer_count)]


def palette_swap(image: Image.Image, p1c: tuple[int], p2c: tuple[int]):
    rgba = np.array(image)
    r, g, b, a = rgba.T
    base1 = PALETTE_BASE_COLORS[0]
    base2 = PALETTE_BASE_COLORS[1]
    target_areas1 = (r == base1[0]) & (g == base1[1]) & (b == base1[2])
    target_areas2 = (r == base2[0]) & (g == base2[1]) & (b == base2[2])
    rgba[..., :-1][target_areas1.T] = p1c
    rgba[..., :-1][target_areas2.T] = p2c
    return Image.fromarray(rgba)


def do_directory_bake(image_dir: Path):
    print("BAKE", image_dir.name)
    relative_dir = image_dir.relative_to(IMAGE_DIR)
    print(relative_dir)
    # print("FILES TO BAKE", list(image_dir.iterdir()))
    frames = FrameGetter()
    for image_fn in image_dir.iterdir():
        frame = None
        if "_" in image_fn.stem:
            layer, frame = image_fn.stem.split("_")
            layer = int(layer)
            frame = int(frame)
        else:
            layer = image_fn.stem
            layer = int(layer)
        frames.add_frame(image_fn, layer, frame)
    print(frames.d)

    for p1i, p1c in enumerate(PALETTE_AVAILABLE_COLORS):
        for p2i, p2c in enumerate(PALETTE_AVAILABLE_COLORS):
            for i, frame_images in enumerate(frames.iterate()):
                destination_fn = DEST_DIR / relative_dir / f"{p1i}_{p2i}" / f"{i}.png"
                if destination_fn.exists():
                    continue
                else:
                    destination_fn.parent.mkdir(exist_ok=True, parents=True)
                print(i, frame_images)
                print("to", destination_fn)
                canvas = palette_swap(Image.open(frame_images[0]), p1c, p2c)
                for additional_layer in frame_images[1:]:
                    canvas.alpha_composite(palette_swap(Image.open(additional_layer), p1c, p2c))
                canvas.save(destination_fn)
    print("---")
    print("")


def bake_palettes():
    for source_dirname in SOURCE_DIRS:
        source_dir = IMAGE_DIR / source_dirname
        subdirs = list(source_dir.iterdir())
        while subdirs:
            subdir = subdirs.pop()
            files_in_dir = list(subdir.iterdir())
            if any(f.suffix == ".png" for f in files_in_dir):
                do_directory_bake(subdir)
            else:
                subdirs.extend(files_in_dir)
    # for p1 in PALETTE_AVAILABLE_COLORS:
    #     for p2 in PALETTE_AVAILABLE_COLORS:
    #         pass


if __name__ == "__main__":
    bake_palettes()
