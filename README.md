Fugue-2x icons
==============

This is a 2x upscaled version of the [Fugue icon set](https://p.yusukekamiyamane.com/),
a set of 3,750 icons by Yusuke Kamiyamane.

This repository contains 32x32 upscaled versions of all original 16x16 Fugue icons. As
such, these icons are appropriate for use at small sizes on high-DPI displays, e.g. at a
size of 16x16 "logical" pixels with 2x scaling, equal to 32x32 physical pixels.

When rebinned to 16x16 physical pixels, these icons look near-identical to the original
16x16 Fugue icons, so there is no need to ship both 16x16 and 32x32 images if the UI
toolkit can rebin them for low-DPI screens (though downsampling that is not rebinning
may not give acceptable results).

The Fugue icon set is licensed under a [creative-commons attribution
license](http://creativecommons.org/licenses/by/3.0/), and may be used with
[attribution](https://p.yusukekamiyamane.com/icons/attribution/) to the author. If you
do not wish to provide attribution, you may [purchase a
license](https://p.yusukekamiyamane.com/icons/license/).

The code in this repository is licensed under the MIT license - see
[`LICENSE-CODE.md`](LICENSE-CODE.md).

[**Preview all
icons**](https://github.com/chrisjbillington/fugue-2x-icons/raw/master/all-2x.png) (9MB
6036x5346 png)

[**Download Fugue-2x icons**](http://github.com/chrisjbillington/fugue-2x-icons/archive/master.zip)

----------

The below shows example icons at 16x16 logical pixels. This will be displayed by your
browser with 32x32 physical pixels only if you are viewing this page at 2x DPI scaling
and 100% zoom level. Otherwise they may appear with reduced detail or blurring.

[<img src="./mini-preview-icons-2x.png" width="622"/>
  ](https://github.com/chrisjbillington/fugue-2x-icons/raw/master/mini-preview-icons-2x.png)

The below shows some of the above icons at twice the scale (32x32 logical pixels), in
order to show full detail if you are viewing this page with 1x DPI scaling. Otherwise,
they may look pixelated.

[<img src="./mini-preview-icons-2x-lodpi.png" width="746"/>
  ](https://github.com/chrisjbillington/fugue-2x-icons/raw/master/mini-preview-icons-2x-lodpi.png)

Comparison
----------

Here is an example showing some of the original 16x16 Fugue icons and their 32x32
upscaled equivalents, all displayed at 32x32 logical pixels:

[<img src="./comparison.png" width="576"/>
  ](https://github.com/chrisjbillington/fugue-2x-icons/raw/master/comparison.png)

Why?
----

Screens have a higher DPI now than they used to, but Fugue remains the most
comprehensive and consistent icon set, appropriate for use at small sizes in desktop
applications, that I know of. Whilst large svg icon sets exist, they are often not drawn
with the pixel-grid in mind causing blurriness when rendered at small sizes, or they are
monochrome and symbolic only, or they have an inappropriate level of detail for use at
small sizes, or they lack consistency.

Although Yusuke Kamiyamane hand-drew all Fugue icons originally at a 32x32 resolution,
he did so in a style that was optimised for how the icons would appear after downscaling
to 16x16 . As such there is a certain blockiness to these 32x32 icons (available as
photoshop files in the Fugue
[source](https://p.yusukekamiyamane.com/icons/downloads/fugue-icons-3.5.6-src.zip)) that
makes them less than ideal for use directly.

It turns out that with some trial-and-error, deep-learning-based upscaling software can
now be coaxed into producing quite good results for this icon set. So here we are.

Methodology
-----------

The icons were upscaled using
[`waifu2x-ncnn-vulkan`](https://github.com/nihui/waifu2x-ncnn-vulkan), a
neural-network-based upsampler trained on anime-style art.

This required some tricks.

Firstly, because `waifu2x` does not deal well with transparency, two versions of the
icons are upscaled, each with the transparent background replaced with a different solid
colour. After upscaling the two images, some pixel maths can be used to remove the
backgrounds and recover an upscaled image with correct transparency.

Secondly, `waifu2x` dealt much better with the icons when they were all placed together
in one large image. Perhaps this gives the neural network more context than each icon
individually, since they are all a similar style.

Thirdly, `waifu2x` didn't deal well with the tiny overlay icons used in icon variants.
These were instead added to the base icons after upscaling, using hand-tweaked versions
of the small overlay icons.

Rebuilding the icons
--------------------

If you just want to use the icons, they are already built and available as files in this
repository, so you don't need to rebuild them. This is just for reference.

The script used to upscale the icons from the original Fugue source is `upscale.py`. To
run it, you'll need the following requirements:

* Python with the `numpy` and `pillow` packages installed
* [`waifu2x-ncnn-vulkan`](https://github.com/nihui/waifu2x-ncnn-vulkan)
* [`imagemagick`](https://imagemagick.org/index.php)

Then run:

```bash
python upscale.py
```

Tested on Arch Linux with `waifu2x-ncnn-vulkan` version `20220728`, `imagemagick`
version`7.1.0` and Python `3.10.7`. This took seven minutes on my system.
