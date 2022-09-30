from pathlib import Path
from subprocess import call
from PIL import Image

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


def download_and_unzip():
    """Download and unzip the fugue icon set source"""
    FUGUE_ZIP = Path(FUGUE_URL.split('/')[-1])
    FUGUE = Path('fugue')
    if not FUGUE_ZIP.exists():
        call(['wget', FUGUE_URL])
    if not FUGUE.exists():
        call(['unzip', FUGUE_ZIP, '-d', FUGUE])


def get_icon_list(folder, include_variants=True):
    """Return a list of all the icon files in the given path, optionally including
    'variant' icons (those with overlaid smaller icons).
    """
    path = Path('fugue', folder)
    if include_variants:
        icons = [p for p in path.iterdir()]
    else:
        icons = [p for p in path.iterdir() if '--' not in p.name]
        # This is the only icon with a double-hyphen that is not a 'variant' icon. All
        # other variant icons are excluded by virtue of containing a double hyphen
        icons.append(path / 'exclamation--frame.png')
    icons.sort()
    return icons


def make_montage(icons, output_name, background_colour="none"):
    """Make a grid of the given icons 50 columns wide with a 2px border around each
    icon"""
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


def add_variants(folder, outdir):
    """Apply overlays to produce variant icons. We have high-res versions of the overlay
    icons used for the variants already, so this does a better job than getting the
    upscaler to work with the variant icons directly"""

    # Make a horizontally-flipped pencil overlay icon:
    mirrored_pencil = tmp / "pencil-mirrored.png"
    if not mirrored_pencil.exists():
        call(['convert', '-flop', 'fugue/icons-shadowless/pencil.png', mirrored_pencil])

    for upscaled_base_icon in list(outdir.iterdir()):
        for variant in VARIANTS:
            variant_name = f"{upscaled_base_icon.stem}--{variant}.png"
            base_icon = Path("fugue", folder, upscaled_base_icon.name)
            variant_icon = Path("fugue", folder, variant_name)
            # Does this variant exist?
            if not variant_icon.exists():
                continue
            # Determine which quadrant of the image the overlay icon is in, by taking a
            # difference image and rebinning to 2x2 px
            base_image = np.array(Image.open(base_icon))
            variant_image = np.array(Image.open(variant_icon))
            difference_image = abs(variant_image - base_image).mean(axis=-1)
            q = rebin(difference_image, (2, 2))

            # Compose the overlay icon on top:
            if variant == 'pencil' and upscaled_base_icon.stem in MIRRORED_PENCILS:
                overlay_filename = mirrored_pencil
            else:
                overlay_filename = f"fugue/icons-shadowless/{variant}.png"
            upscaled_variant_icon = outdir / variant_name
            gravity = ['NorthWest', 'NorthEast', 'SouthWest', 'SouthEast'][q.argmax()]

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

    # There is one icon with a variant that does not follow the naming conventions:
    overlay_filename = "fugue/icons-shadowless/pencil.png"
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
    # to upscale. We'll then extract the results

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


    add_variants(folder, outdir)


if __name__ == '__main__':
    tmp = Path('tmp')
    tmp.mkdir(exist_ok=True)
    download_and_unzip()
    upscale_icon_set('icons')
    upscale_icon_set('icons-shadowless')
