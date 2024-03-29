from pathlib import Path
from subprocess import call
from urllib.request import urlopen
from zipfile import ZipFile
from PIL import Image, ImageFont, ImageDraw

import numpy as np

FUGUE_URL = "https://p.yusukekamiyamane.com/icons/downloads/fugue-icons-3.5.6-src.zip"

VARIANTS = [
    "arrow",
    "exclamation",
    "minus",
    "pencil",
    "plus",
]


# Icons whose "pencil" variant has a horizontally-flipped pencil
MIRRORED_PENCILS = [
    "ear",
    "tag",
    "leaf",
    "pill",
    "plug",
    "broom",
    "eraser",
    "puzzle",
    "ticket",
    "bookmark",
    "lightning",
]

# Icons whose overlays have the main icon horixontally displaced by some number of
# pixels
ROLLED_VARIANTS = {
    'key': {'plus': 2, 'arrow': 3, 'minus': 2, 'pencil': 3, 'exclamation': 3},
    'funnel': {'plus': 1, 'arrow': 1, 'minus': 1, 'pencil': 1, 'exclamation': 1},
    'music': {'plus': 3, 'arrow': 3, 'minus': 3, 'pencil': 3, 'exclamation': -2}
}

# Icons whose name have a common prefix with the icon above them in the icon list, but
# which should not be treated as sharing a prefix with them (for the purposes of
# rendering all-2x.png)
PREFIX_EXCEPTIONS = [
    'home-for-sale-sign',
    'ice-cream',
    'road-sign',
    'sql-join',
    'ui-panel-resize',
]


def download_and_unzip():
    """Download and unzip the fugue icon set source"""
    FUGUE_ZIP = tmp / 'fugue.zip'
    FUGUE = tmp / 'fugue'
    if not FUGUE_ZIP.exists():
        print(f"downloading {FUGUE_URL} as {FUGUE_ZIP}")
        with open(FUGUE_ZIP, 'wb') as f:
            f.write(urlopen(FUGUE_URL).read())
    if not FUGUE.exists():
        print(f"decompressing {FUGUE_ZIP} to {FUGUE}")
        zipfile = ZipFile(FUGUE_ZIP)
        zipfile.extractall(path=FUGUE)


def get_icon_list(folder, include_variants=True):
    """Return a list of all the icon files in the given path, optionally including
    'variant' icons (those with overlaid smaller icons).
    """
    icon_filenames = (tmp / 'fugue/FILENAME.txt').read_text('utf8').splitlines()
    if folder == 'icons-shadowless':
        # In the shadowless icons, this one is called 'application-plus-sub', probably
        # in error:
        i = icon_filenames.index('application-sub.png')
        icon_filenames[i] = 'application-plus-sub.png'
    path = tmp / 'fugue' / folder
    if include_variants:
        icons = [path / name for name in icon_filenames]
    else:
        icons = [path / name for name in icon_filenames if '--' not in name]
        # This is the only icon with a double-hyphen that is not a 'variant' icon. All
        # other variant icons are excluded by virtue of containing a double hyphen
        icons.append(path / 'exclamation--frame.png')
    return icons


def make_montage(icons, output_name, background_colour="none"):
    """Make a grid of the given icons 50 columns wide with a 2px border around each
    icon"""
    print(f"Creating montage {output_name}")
    call(
        [
            'magick',
            'montage',
            '-tile',
            '50x0',
            '-background',
            background_colour,
            '-geometry',
            '+2+2',
            *icons,
            output_name,
        ]
    )


def upscale(infile):
    print(f"Upscaling {infile}")
    outfile = infile.parent / f"{infile.stem}-2x.png"
    call(['waifu2x-ncnn-vulkan', '-i', infile, '-o', outfile, '-n', '-1', '-x'])
    return outfile


def rebin(arr, new_shape):
    shape = (
        new_shape[0],
        arr.shape[0] // new_shape[0],
        new_shape[1],
        arr.shape[1] // new_shape[1],
    )
    return arr.reshape(shape).mean(-1).mean(1)


def roll(im, delta):
    """Roll an image sideways."""
    xsize, ysize = im.size
    delta = delta % xsize
    part1 = im.crop((0, 0, delta, ysize))
    part2 = im.crop((delta, 0, xsize, ysize))
    im.paste(part1, (xsize - delta, 0, xsize, ysize))
    im.paste(part2, (0, 0, xsize - delta, ysize))

    return im

def make_variants(folder):
    """Apply overlays to produce variant icons. We have high-res versions of the overlay
    icons used for the variants already, so this does a better job than getting the
    upscaler to work with the variant icons directly"""

    print(f"Making variants for {folder}")
    outdir = Path(f"{folder}-2x")

    # Make a horizontally-flipped pencil overlay icon:
    mirrored_pencil = tmp / "pencil-mirrored.png"
    if not mirrored_pencil.exists():
        call(
            [
                'convert',
                '-flop',
                tmp / 'fugue/icons-shadowless/pencil.png',
                mirrored_pencil,
            ]
        )

    for upscaled_base_icon in list(outdir.iterdir()):
        base_icon = Path(tmp, "fugue", folder, upscaled_base_icon.name)
        base_name = upscaled_base_icon.stem

        for variant in VARIANTS:
            variant_name = f"{base_name}--{variant}.png"
            variant_icon = Path(tmp, "fugue", folder, variant_name)
            # Does this variant exist?
            if not variant_icon.exists():
                continue

            # Create a version of the upscaled base icon horizontally displaced if
            # needed:
            if base_name in ROLLED_VARIANTS:
                img = Image.open(upscaled_base_icon)
                img = roll(img, 2 * ROLLED_VARIANTS[base_name][variant])
                base_icon_file = tmp / f'{folder}-{base_name}-{variant}-rolled.png'
                img.save(base_icon_file)
            else:
                base_icon_file = upscaled_base_icon

            # The original base icon, also potentially horizontally displaced
            base_image = Image.open(base_icon)
            if base_name in ROLLED_VARIANTS:
                base_image = roll(base_image, ROLLED_VARIANTS[base_name][variant])
            base_image = np.array(base_image)

            # Multiply through by alpha
            base_image = base_image[:, :, :3] * (base_image[:, :, 3, np.newaxis] / 255)

            # Determine which quadrant of the image the overlay icon is in, by taking a
            # difference image and rebinning to 2x2 px
            variant_image = np.array(Image.open(variant_icon))
            # Multiply through by alpha
            variant_image = variant_image[:, :, :3] * (
                variant_image[:, :, 3, np.newaxis] / 255
            )
            difference_image = abs(variant_image - base_image).mean(axis=-1)
            q = rebin(difference_image, (2, 2))

            # Compose the overlay icon on top:
            if variant == 'pencil' and base_name in MIRRORED_PENCILS:
                overlay_filename = "overlays/pencil-mirrored.png"
            else:
                overlay_filename = f"overlays/{variant}.png"
            upscaled_variant_icon = outdir / variant_name
            gravity = ['NorthWest', 'NorthEast', 'SouthWest', 'SouthEast'][q.argmax()]

            call(
                [
                    'magick',
                    'composite',
                    '-gravity',
                    gravity,
                    overlay_filename,
                    base_icon_file,
                    upscaled_variant_icon,
                ]
            )

    # There is one icon with a variant that does not follow the naming conventions:
    overlay_filename = "overlays/pencil.png"
    upscaled_base_icon = outdir / "layout-hf-2.png"
    upscaled_variant_icon = outdir / "layout-design.png"
    gravity = "SouthWest"
    call(
        [
            'magick',
            'composite',
            '-gravity',
            gravity,
            overlay_filename,
            upscaled_base_icon,
            upscaled_variant_icon,
        ]
    )


def upscale_icon_set(folder):
    # We use the program waifu2x-ncnn-vulkan to upscale the icons, and we use
    # imagemagick for image manipulations. waifu2x doesn't deal well with transparancy,
    # so we use a trick to have it operate on two images with different solid
    # backgrounds, and then recover the transparancy as described here:
    # https://imagemagick.org/Usage/masking/#two_background

    # waifu2x works best on a single image with all the icons in it, I suppose it gives
    # it more context to work with. So let's make single images containing all the icons
    # to upscale. We'll then extract the results.

    base_icons = get_icon_list(folder, include_variants=False)
    green_montage = tmp / f"{folder}-montage-green.png"
    magenta_montage = tmp / f"{folder}-montage-magenta.png"
    make_montage(base_icons, green_montage, background_colour='green')
    make_montage(base_icons, magenta_montage, background_colour='magenta')

    # Do the upscaling
    green_montage_2x = upscale(green_montage)
    magenta_montage_2x = upscale(magenta_montage)

    # Do the background recovery:
    alpha_image = tmp / f"{folder}-2x-alpha.png"

    print(
        "Reconstructing image with alpha channel from"
        + f"{green_montage_2x} and {magenta_montage_2x}"
    )

    # Extract alpha
    call(
        [
            'magick',
            green_montage_2x,
            magenta_montage_2x,
            '-compose',
            'difference',
            '-composite',
            '-separate',
            '-evaluate-sequence',
            'max',
            '-auto-level',
            '-negate',
            alpha_image,
        ]
    )
    # Invert alpha composition to obtain original image. Do this with both images and
    # average the result
    upscaled_images = [green_montage_2x, magenta_montage_2x]
    decomposed_images = [s.parent / f"{s.stem}-decomposed.png" for s in upscaled_images]
    montage_2x = tmp / f"{folder}-2x.png"
    for upscaled_image, decomposed_image in zip(upscaled_images, decomposed_images):
        call(
            [
                'magick',
                upscaled_image,
                alpha_image,
                '-alpha',
                'Off',
                '-fx',
                "v==0 ? 0 : u/v - u.p{0,0}/v + u.p{0,0}",
                alpha_image,
                '-compose',
                'Copy_Opacity',
                '-composite',
                decomposed_image,
            ]
        )
    call(['convert', '-average', *decomposed_images, montage_2x])

    # Remove alpha garbage (nozero pixel values when alpha is near-zero):
    call(['convert', montage_2x, '-fx', 'a<2/128 ? 0 : u', montage_2x])

    print(f"Extracting individual icons from montage {montage_2x}")

    # Crop out the individual icons to separate files once more
    outdir = Path(f"{folder}-2x")
    outdir.mkdir(exist_ok=True)
    call(
        [
            'convert',
            montage_2x,
            '-crop',
            '40x40',
            '+repage',
            '+adjoin',
            outdir / '%04d.png',
        ]
    )
    call(
        [
            'convert',
            *sorted(outdir.iterdir()),
            '-gravity',
            'center',
            '-crop',
            '32x32+0+0',
            '+repage',
            outdir / '%04d.png',
        ]
    )

    # Rename them to have the correct names
    for i, icon in enumerate(base_icons):
        Path(outdir, f"{i:04d}.png").rename(outdir / icon.name)
    # Delete blanks:
    while True:
        i += 1
        try:
            Path(outdir, f"{i:04d}.png").unlink()
        except FileNotFoundError:
            break


def make_preview(folder, mini_preview=False):

    all_icons = [p.stem for p in get_icon_list(folder)]

    COPYRIGHT_WIDTH = 2 *350
    COPYRIGHT_HEIGHT = 2 * 110

    if mini_preview:
        N_ROWS = 13
        N_COLS = 5
        IMAGE_PADDING = 0
        RIGHT_CROP = 6
        BOTTOM_PADDING = 0
        output_file = f"mini-preview-{folder}-2x.png"
        icons = Path('mini-preview-icons.txt').read_text('utf8').splitlines()
    else:
        N_ROWS = 150
        N_COLS = 24
        IMAGE_PADDING = 18
        RIGHT_CROP = 0
        BOTTOM_PADDING = COPYRIGHT_HEIGHT
        output_file = f"all-2x{folder.lstrip('icons')}.png"
        icons = all_icons

    ICON_SIZE = 32
    ICON_PADDING = 2

    TEXT_PADDING = 8
    TEXT_LENGTH = 198

    FONT_SIZE = 19

    print(f"Making {output_file}")

    image = Image.new(
        "RGBA",
        (
            N_COLS * (ICON_SIZE + 2 * ICON_PADDING + TEXT_LENGTH + 2 * TEXT_PADDING)
            + 2 * IMAGE_PADDING
            - RIGHT_CROP,
            N_ROWS * (ICON_SIZE + 2 * ICON_PADDING)
            + 2 * IMAGE_PADDING
            + BOTTOM_PADDING,
        ),
        (255, 255, 255, 0),
    )
    draw = ImageDraw.Draw(image)
    draw.fontmode = "L"
    font = ImageFont.truetype("Ubuntu-R.ttf", FONT_SIZE)

    x = IMAGE_PADDING
    y = IMAGE_PADDING
    

    # Figure out the prefixes for each icon:
    prefixes = {}
    current_prefix = ''
    for icon in all_icons:
        if icon in PREFIX_EXCEPTIONS:
            current_prefix = icon
        elif icon.startswith(current_prefix + '-'):
            prefixes[icon] = current_prefix
        else:
            current_prefix = icon

    for i, icon in enumerate(icons):
        icon_image = Image.open(f'{folder}-2x/{icon}.png')
        image.paste(icon_image, (x + ICON_PADDING, y + ICON_PADDING))
        text = icon
        while draw.textlength(text=text, font=font) > TEXT_LENGTH:
            text = text[:-2] + '…'

        # Does the icon have a prefix?
        if icon in prefixes:
            prefix = prefixes[icon]
            suffix = text[len(prefix):]
        else:
            prefix, suffix = icon, None
        draw.text(
            (
                x + 2 * ICON_PADDING + ICON_SIZE + TEXT_PADDING,
                y + ICON_PADDING + ICON_SIZE // 2,
            ),
            prefix,
            (0, 0, 0),
            anchor="lm",
            font=font,
        )
        if suffix:
            text1_len = draw.textlength(text=prefix, font=font)
            draw.text(
                (
                    x + 2 * ICON_PADDING + ICON_SIZE + TEXT_PADDING + text1_len,
                    y + ICON_PADDING + ICON_SIZE // 2,
                ),
                suffix,
                (160, 160, 160),
                anchor="lm",
                font=font,
            )

        y += ICON_SIZE + 2 * ICON_PADDING

        if i % N_ROWS == N_ROWS - 1:
            x += ICON_SIZE + 2 * ICON_PADDING + TEXT_LENGTH + 2 * TEXT_PADDING
            y = IMAGE_PADDING

    image.save(output_file)

    if mini_preview:
        # Crop to half width for use in README on lodpi displays:
        lodpi_output_file = output_file.replace('.png', '-lodpi.png')
        print(f"Making {lodpi_output_file}")
        call(
            [
                'convert',
                output_file,
                '-crop',
                f"{int(3 / 5 * image.width)}x{image.height}+0+0",
                '+repage',
                lodpi_output_file,
            ]
        )
        # Flatten
        call(
            [
                'convert',
                lodpi_output_file,
                '-background',
                'white',
                '-flatten',
                lodpi_output_file,
            ]
        )
        # Double the pixel density so on hidpi displays its blocky rather than blurry:
        call(
            [
                'convert',
                lodpi_output_file,
                '-filter',
                'box',
                '-resize',
                '200%',
                lodpi_output_file,
            ]
        )

    else:
        # Add copyright:
        copyright = tmp / "copyright.png"
        call(
            [
                'convert',
                tmp / 'fugue/all.png',
                '-gravity',
                'SouthWest',
                '-crop',
                f"{COPYRIGHT_WIDTH//2}x{COPYRIGHT_HEIGHT//2}+0+0",
                '+repage',
                copyright,
            ]
        )
        call(['convert', copyright, '-background', 'white', '-flatten', copyright])
        copyright_2x = upscale(copyright)
        call(
                [
                    'magick',
                    'composite',
                    '-gravity',
                    'SouthWest',
                    copyright_2x,
                    output_file,
                    output_file,
                ]
            )

    # Flatten
    call(['convert', output_file, '-background', 'white', '-flatten', output_file])


def make_comparison():

    output_name = "comparison.png"
    print(f"making {output_name}")
    names = Path('mini-preview-icons.txt').read_text('utf8').splitlines()

    # Make it a multiple of 8
    names.remove('user-detective')

    icons = []
    for name in names:
        icons.append(tmp / f'fugue/icons/{name}.png')
        icons.append(f'icons-2x/{name}.png')
    call(
        [
            'magick',
            'montage',
            '-tile',
            '16x0',
            '-background',
            'white',
            '-geometry',
            '64x64+2+2',
            '-filter',
            'box',
            '-gravity',
            'North',
            *icons,
            output_name,
        ]
    )

if __name__ == '__main__':
    tmp = Path('tmp')
    tmp.mkdir(exist_ok=True)
    download_and_unzip()

    upscale_icon_set('icons')
    make_variants('icons')
    make_preview('icons')

    upscale_icon_set('icons-shadowless')
    make_variants('icons-shadowless')
    make_preview('icons-shadowless')

    make_preview('icons', mini_preview=True)
    make_comparison()
