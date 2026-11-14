# References

## In plain words

This page is the shared list of sources for the documentation. Every fact,
number and formula in these pages should point to an entry here, or be
marked as something worked out in this project or assumed. The rules are in
the [documentation standard](plan.md#documentation-standard).

## How claims are labelled

| Label | Meaning |
|---|---|
| **[key]** | Taken from the source with that key in the list below |
| **Derived here** | Worked out in this project from stated starting points. The page or code that does the working is named, so it can be checked. |
| **Estimate** | A number from the project's own simplified model. Good for comparing options, not yet confirmed by a more exact simulation. |
| **Assumption** | Chosen to make progress, with no source. Listed so it can be challenged. |
| **Unverified** | Believed from general knowledge or a secondary source, not yet checked against a primary one. To be sourced or removed. |

Entries marked "checked" were matched against a bibliographic database when
they were added. That confirms the work exists as cited. It does not confirm
that the page number or the specific claim has been checked against the text
unless the entry says so.

## Textbooks and standard methods

| Key | Source | Used for |
|---|---|---|
| Goodman | J. W. Goodman, *Introduction to Fourier Optics*, first edition 1968, later editions by Roberts and W. H. Freeman. Checked. | Light crossing a gap as a spread of plane waves; detail finer than the wavelength as evanescent waves; transfer functions of apertures |
| BornWolf | M. Born and E. Wolf, *Principles of Optics*, Pergamon and later Cambridge University Press. Existence matched with low confidence by the database; a standard text. | The grating equation, which gives the slanted-light limit; reflection at a flat interface |
| Janesick | J. R. Janesick, *Photon Transfer*, SPIE Press, 2007. [doi:10.1117/3.725073](https://doi.org/10.1117/3.725073). Checked. | The sensor noise model: photon noise, read noise, full well |
| HarwitSloane | M. Harwit and N. J. A. Sloane, *Hadamard Transform Optics*, Academic Press, 1979. [doi:10.1016/b978-0-12-330050-8.x5001-x](https://doi.org/10.1016/b978-0-12-330050-8.x5001-x). Checked. | When combining many measurements in a coded pattern gains over taking them one at a time, and why the gain vanishes when the noise comes from the light itself |
| Raskar2006 | R. Raskar, A. Agrawal and J. Tumblin, "Coded exposure photography: motion deblurring using fluttered shutter", ACM Transactions on Graphics, 2006. [doi:10.1145/1141911.1141957](https://doi.org/10.1145/1141911.1141957). Checked. | Coded exposure as a way to keep motion blur reversible |
| HestenesStiefel | M. R. Hestenes and E. Stiefel, "Methods of conjugate gradients for solving linear systems", Journal of Research of the National Bureau of Standards, 1952. [doi:10.6028/jres.049.044](https://doi.org/10.6028/jres.049.044). Checked. | The iterative solver used for the main reconstruction |
| vanHeel2005 | M. van Heel and M. Schatz, "Fourier shell correlation threshold criteria", Journal of Structural Biology, 2005. [doi:10.1016/j.jsb.2005.05.009](https://doi.org/10.1016/j.jsb.2005.05.009). Checked. | The resolution measure used to judge reconstructions |
| GuizarSicairos2008 | M. Guizar-Sicairos, S. T. Thurman and J. R. Fienup, "Efficient subpixel image registration algorithms", Optics Letters, 2008. [doi:10.1364/ol.33.000156](https://doi.org/10.1364/ol.33.000156). Checked. | Measuring the shift between frames to a fraction of a pixel |
| Maiden2009 | A. M. Maiden and J. M. Rodenburg, "An improved ptychographical phase retrieval algorithm for diffractive imaging", Ultramicroscopy, 2009. [doi:10.1016/j.ultramic.2009.05.012](https://doi.org/10.1016/j.ultramic.2009.05.012). Checked. | Phase recovery from overlapping scans |
| Zheng2013 | G. Zheng, R. Horstmeyer and C. Yang, "Wide-field, high-resolution Fourier ptychographic microscopy", Nature Photonics, 2013. [doi:10.1038/nphoton.2013.187](https://doi.org/10.1038/nphoton.2013.187). Checked. | Slanted light from many directions combined by computation into a wider aperture |

## The sensor and its layers

| Key | Source | Used for |
|---|---|---|
| R1 | Raspberry Pi, "Camera" hardware documentation. <https://www.raspberrypi.com/documentation/accessories/camera.html> | Sensor models, pixel counts, pixel pitch, listed modes |
| R2 | Matthews et al., "Laser de-Bayering of low cost image sensors", arXiv:1901.03807. <https://arxiv.org/abs/1901.03807> | Electron-microscope cross-section of the IMX219: order of the layers on a pixel |
| R3 | Bowman et al., "Flat-field and colour correction for the Raspberry Pi camera module", arXiv:1911.13295. <https://arxiv.org/abs/1911.13295> | Microlenses bonded to the chip and shifted towards the centre near the edges |
| R4 | E. Orbach, "Debayering Raspberry Pi camera", 2016. <https://eladorbach.blogspot.com/2016/05/debayering-raspberry-pi-camera.html> | Practical reports of removing the lens holder and filter layers (first-generation module) |
| R5 | Hackaday, "Using a laser to blast away a Bayer array", 2021. <https://hackaday.com/2021/08/09/using-a-laser-to-blast-away-a-bayer-array> | Practical report of removing the filter by laser (first-generation module) |
| LinuxIMX219 | Linux kernel driver for the IMX219, `drivers/media/i2c/imx219.c`. <https://github.com/torvalds/linux/blob/master/drivers/media/i2c/imx219.c> | Registers the sensor exposes, pixel clock and line length, from which the 18.9 µs line time is derived. Read from memory of the driver, not re-read line by line: **Unverified** until data item R1 of the plan is done. |

## Closest earlier instruments and reconstruction methods

| Key | Source | Used for |
|---|---|---|
| Heng2006 | Heng et al., "Optofluidic microscopy: a method for implementing a high resolution optical microscope on a chip", Lab on a Chip, 2006. [doi:10.1039/b604676b](https://doi.org/10.1039/b604676b) | A lensless sensor with a tilted line of openings and a sample moving at constant speed |
| Cui2008 | Cui et al., "Lensless high-resolution on-chip optofluidic microscopes for Caenorhabditis elegans and cell imaging", PNAS, 2008. [doi:10.1073/pnas.0804612105](https://doi.org/10.1073/pnas.0804612105) | The same family of instrument |
| Zheng2010 | Zheng et al., "Sub-pixel resolving optofluidic microscope for on-chip cell imaging", Lab on a Chip, 2010. [doi:10.1039/c0lc00213e](https://doi.org/10.1039/c0lc00213e) | Sub-pixel reconstruction from samples moving over bare pixels |
| Zheng2011 | Zheng et al., "The ePetri dish, an on-chip cell imaging platform based on subpixel perspective sweeping microscopy", PNAS, 2011. [doi:10.1073/pnas.1110681108](https://doi.org/10.1073/pnas.1110681108) | Sub-pixel shifts obtained by moving the light source |
| Fruchter2002 | Fruchter and Hook, "Drizzle: a method for the linear reconstruction of undersampled images", PASP, 2002. [doi:10.1086/338393](https://doi.org/10.1086/338393) | The standard shift-and-add method |
| Farsiu2004 | Farsiu et al., "Fast and robust multiframe super resolution", IEEE Transactions on Image Processing, 2004. [doi:10.1109/tip.2004.834669](https://doi.org/10.1109/tip.2004.834669) | Regularised reconstruction from many frames |

## Reference lists of the other pages

Three pages keep their own numbered lists, which are part of this
bibliography:

- [Optical elements, section 14](optical-elements.md#14-references), keys
  O1 onwards.
- [Reconstruction methods, section 11](reconstruction-methods.md#11-references).
- [Calibration and test methods, section 14](calibration-and-test.md#14-references),
  keys T1 onwards.

New sources are added here, or to those lists for those pages, in the same
pull request as the claim that needs them.
