from pathlib import Path
from PIL import Image, ImageFont, ImageDraw


def get_icon_list(folder, include_variants=True):
    """Return a list of all the icon files in the given path, optionally including
    'variant' icons (those with overlaid smaller icons).
    """
    path = Path('tmp') / 'fugue' / folder
    if include_variants:
        icons = [p for p in path.iterdir()]
    else:
        icons = [p for p in path.iterdir() if '--' not in p.name]
        # This is the only icon with a double-hyphen that is not a 'variant' icon. All
        # other variant icons are excluded by virtue of containing a double hyphen
        icons.append(path / 'exclamation--frame.png')
    icons.sort(key=lambda p: p.stem)
    return icons


def make_all_dot_png(folder):
    N_ROWS = 150
    N_COLS = 24

    ICON_SIZE = 16
    ICON_PADDING = 1
    IMAGE_PADDING = 9

    TEXT_PADDING = 4
    TEXT_SIZE = 100

    image = Image.new(
        "RGBA",
        (
            N_COLS * (ICON_SIZE + 2 * ICON_PADDING + TEXT_SIZE + 2 * TEXT_PADDING)
            + 2 * IMAGE_PADDING,
            N_ROWS * (ICON_SIZE + 2 * ICON_PADDING) + 2 * IMAGE_PADDING,
        ),
        (255, 255, 255),
    )
    draw = ImageDraw.Draw(image)
    draw.fontmode = "L"
    font = ImageFont.truetype("Ubuntu-R.ttf", 10)

    x = IMAGE_PADDING
    y = IMAGE_PADDING
    icons = [p.stem for p in get_icon_list(folder)]
    for i, icon in enumerate(icons):
        icon_image = Image.open(f'tmp/fugue/{folder}/{icon}.png')
        image.paste(icon_image, (x + ICON_PADDING, y + ICON_PADDING), mask=icon_image)
        text = icon
        while draw.textlength(text=text, font=font) > TEXT_SIZE:
            text = text[:-2] + '…'

        text1, *text2 = text.split('-')
        if text2:
            text2 = '-' + '-'.join(text2)
        draw.text(
            (
                x + 2 * ICON_PADDING + ICON_SIZE + TEXT_PADDING,
                y + ICON_PADDING + ICON_SIZE // 2,
            ),
            text1,
            (0, 0, 0),
            anchor="lm",
            font=font,
        )
        if text2:
            text1_len = draw.textlength(text=text1, font=font)
            draw.text(
                (
                    x + 2 * ICON_PADDING + ICON_SIZE + TEXT_PADDING + text1_len,
                    y + ICON_PADDING + ICON_SIZE // 2,
                ),
                text2,
                (128, 128, 128),
                anchor="lm",
                font=font,
            )

        y += ICON_SIZE + 2 * ICON_PADDING

        if i % N_ROWS == N_ROWS - 1:
            x += ICON_SIZE + 2 * ICON_PADDING + TEXT_SIZE + 2 * TEXT_PADDING
            y = IMAGE_PADDING
            

    image.save(f"all{folder.lstrip('icons')}.png")

make_all_dot_png("icons")
make_all_dot_png("icons-shadowless")

# 1px border on each icon = 2px in between
# additional 9 pixels at edge
# text baseline is px 4
# text lowecase letters are 5px high
# gap from icon to image is 5px


# Algorithm for figuring out suffixes:
# What's the shortest hyphenated name that exists? That's the base. The rest are suffixes.
