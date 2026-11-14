# Glossary

Plain-language meanings of the terms used across this documentation. Pages
link here the first time they use a term that is not explained on the spot.

| Term | Meaning |
|---|---|
| Acceptance angle | How far from straight ahead light can arrive at a pixel, or at a tube in front of it, and still be detected. The same idea as collection angle. |
| Anchor | A quantity that the scan data cannot fix by itself, so that one outside measurement is needed to pin it: an absolute length, an absolute brightness or an absolute height. |
| Aperture | The opening through which light is collected. A wider opening, or a wider range of angles, lets finer detail through. |
| Approach | One complete way of building and running the instrument: a choice of light, optical parts, gap, sensor, readout, scan, exposure and reconstruction method. |
| Artefact | A false feature in a reconstructed picture that comes from the method and not from the surface. |
| Band (cut-off) | The band is the range of detail sizes a method can carry, from coarse to fine. The cut-off is the finest detail in the band. Detail beyond the cut-off does not reach the sensor. |
| Bayer filter | The pattern of red, green and blue filters laid over the pixels of a colour sensor, one colour per pixel. |
| Beam pair | Two beams from the same laser reaching the surface from different sides at the same time. Where they cross they form fringes. |
| Beam splitter | A part-silvered mirror that divides one beam of light into two. |
| Beat (moiré) | The broad pattern that appears when two fine patterns of nearly the same spacing overlap, as with two net curtains. |
| Benchmark | A fixed set of test scenes, conditions and scoring rules that every approach is run through, so that their results can be compared fairly. |
| Birefringent | Said of a crystal that splits a beam of light into two slightly shifted copies. |
| Blur kernel | The shape that a single point of the surface is smeared into by the time it is recorded. A wide kernel means a blurry picture. |
| Bond wires | The fine wires around the edge of a chip that connect it to its package. They stand higher than the chip surface. |
| Calibration | Measuring a part of the instrument, such as a mask or the light pattern, so that the reconstruction can allow for it. |
| Coherence length | The distance over which the waves of a light source stay in step. The purer the colour, the longer it is: wavelength squared divided by the spread of wavelengths. |
| Coherent light | Light whose waves stay in step with each other, such as laser light. It can form interference patterns. Ordinary lamp light is not coherent. |
| Collection angle | The widest angle, away from straight ahead, at which a pixel still responds to light. |
| Collimated light | A beam whose rays are all parallel. |
| Collimator | A plate of tubes or holes that lets through only light travelling nearly straight along them. |
| Contrast | How much brighter the bright parts of a pattern are than the dark parts. Blur lowers contrast. When it falls below the noise, the pattern is lost. |
| Convolution | The mathematical name for smearing: every point of a picture is replaced by a copy of the blur kernel, and the copies are added up. |
| Cramér-Rao bound | The smallest error that any method could reach when estimating a quantity from noisy data. It is worked out from how strongly the data change when the quantity changes. |
| Deconvolution | Undoing a known blur by computation. |
| Die | The bare piece of silicon that is the sensor chip itself, without its package. |
| Diffraction | The spreading of light into a fan of directions when it meets fine structure. Finer structure sends light out at steeper angles. |
| Diffraction pattern (hologram) | The pattern of ripples that coherent light forms on the sensor after leaving the surface. It holds the detail of the surface in scrambled form. |
| Diffuse (matt) surface | A surface that scatters light in all directions, like paper. The opposite is mirror-like. |
| Diffuse light | Light travelling in all directions, as from a frosted bulb or from a matt surface. |
| Diffuser | A layer that scatters light, like frosted glass. |
| Dither | A small amount of noise, present or added on purpose, that stops rounding from hiding changes smaller than one step of the readout. |
| Diversity | Measurements that differ in kind, such as a different gap, lighting direction or light pattern, and not only in position. Phase recovery needs it. |
| Electromagnetic solver | A program that calculates how light behaves from the basic equations of electricity and magnetism. Slow, and as exact as the description of the materials it is given. |
| Evanescent wave | Light that carries detail finer than the wavelength. It clings to the surface and fades within a fraction of a wavelength, so it never reaches a distant detector. |
| Exposure | The time during which a pixel adds up light for one reading. |
| Far field | Far enough from the surface, many wavelengths, that only ordinary travelling light is left. |
| Feature | A detail on the surface, such as a line of wiring on a chip. |
| Footprint (patch) | The area of surface that one pixel sees, and how strongly it sees each part of it. Another name for the blur kernel seen from the pixel. |
| Forward model | The calculation that predicts what the sensor would record for a given surface. Reconstruction runs it backwards. |
| Fourier ring correlation | A standard test of how fine the trustworthy detail in a reconstruction is, found by checking down to what size it still agrees with the truth or with a second independent reconstruction. |
| Frame | One complete readout of the sensor. |
| Fringes | The regular bright and dark stripes formed where two coherent beams overlap. |
| Full electromagnetic model | A simulation of light as it really is, an electric and magnetic wave, with no simplifications. Slow, but accurate for detail smaller than the wavelength. |
| Gap | The distance between the light-sensitive layer of the sensor and the surface being examined. |
| Gate | The defined set of conditions a simulated approach must pass before any hardware is built for it. |
| Global shutter | A sensor in which every pixel is exposed at the same instant. See rolling shutter. |
| Grating | A plate carrying fine, evenly spaced lines. |
| Held-out data | Readings kept aside and not shown to the reconstruction. A good reconstruction predicts them as well as the readings it was given. |
| Hologram | A recording of the fringes made when light scattered from an object overlaps with an undisturbed reference beam. It holds the phase in a form a camera can record. |
| Identifiable | Said of an unknown that the data can pin down. Two unknowns that can change together without changing any reading are not identifiable separately. |
| Interference | What happens when two light waves overlap. Where they are in step they add and the light is bright. Where they are out of step they cancel and it is dark. |
| Invented detail | Detail in a reconstructed picture that came from the method's assumptions and not from the surface. Also called hallucination. |
| Inverse crime | Testing a reconstruction on data made by the same simplified model that the reconstruction uses, which makes the result look better than it would on real data. |
| Inverse problem | Working out the cause from the effect: here, the surface from the recorded readings. |
| Iteration | One round of an improve-and-check loop. Most reconstruction methods repeat such a round tens or hundreds of times. |
| Iterative | Said of a calculation that guesses an answer, compares it with the data, improves the guess and repeats. |
| Laser diode | A small electronic light source that gives coherent light of a single colour. |
| Least squares | Finding the answer whose predicted measurements differ least from the real ones, judged by the sum of the squared differences. |
| LED | A small electronic light source that gives a band of colour and is not coherent. |
| Lensless | With no lens between the surface and the sensor. |
| Line time | The time a sensor takes to read one row of pixels, 18.9 millionths of a second for the IMX219. |
| Line width | The width of one line of a pattern. With lines and spaces of equal width it is half the period. |
| Linear | Said of a model in which doubling the cause doubles the reading. Such problems can be solved in one pass. |
| Mask (coded mask) | A layer with a fine pattern of clear and dark, or thick and thin, areas, placed in the light path so that the recorded pattern keeps fine detail. |
| Maximum likelihood | Fitting that gives each reading the weight it deserves from the known statistics of its noise, instead of treating all readings alike. |
| Microlens | The tiny lens built on top of each pixel of a sensor to gather light into it. |
| Micrometre (µm) | A thousandth of a millimetre. A human hair is roughly 80 µm across. |
| Mirror-like (specular) surface | A smooth surface that reflects light in one direction, like polished silicon. |
| Mixed states | A description of light, in ptychography, as a mixture of a few patterns instead of one. It accounts for imperfect coherence and for vibration during an exposure. |
| Motion blur | Smearing caused by the sensor moving while a pixel is adding up light. |
| Nanometre (nm) | A thousandth of a micrometre, a millionth of a millimetre. 100 nm is roughly a thousandth of the width of a human hair. |
| Near field | Within a fraction of a wavelength of the surface, where detail finer than the wavelength can still be picked up. |
| Noise | Random variation in the readings that does not come from the surface. Averaging many readings reduces it. |
| Noise floor | The level below which a signal is lost in the noise. |
| Numerical aperture (NA) | A number that says how steep an angle is: the sine of the angle measured from straight ahead, times the refractive index of the medium. In air it lies between 0 and 1. |
| Open pixel | A pixel with nothing in front of it to limit the directions it sees. |
| Period | The distance over which a regular pattern repeats. Lines and spaces each 100 nm wide have a period of 200 nm. |
| Phase | Where a wave is in its cycle. Sensors record brightness only, so phase has to be worked out by computation. |
| Phase recovery | Computing the lost phase of light from brightness readings taken under varied conditions. |
| Photon noise | Noise from the fact that light arrives as separate particles (photons), so that counts vary by chance. It grows as the square root of the light. |
| Photon transfer curve | A plot of the noise in a pixel's reading against its brightness. Its slope gives the number of electrons per count, and its floor gives the read noise. |
| Pixel | One of the light-sensing squares of a sensor. |
| Pixel pitch | The distance from the centre of one pixel to the next, 1.12 µm for the IMX219. |
| Pixel response | How strongly a pixel reacts to light depending on exactly where on the pixel it lands and from what angle it arrives. |
| Polariser | A filter that passes only light vibrating in one direction, as polarising sunglasses do. |
| Prior | Something assumed to be true about the surface before looking at the data, for example that chips have straight edges. |
| Probe | The patch or pattern of light that falls on the surface in ptychography. It can be worked out from the data along with the picture. |
| Ptychography | A method that scans a sample under coherent light, records many overlapping brightness patterns, and computes a sharp picture, including phase, from the overlap. |
| Pulse | A short flash of light. |
| Read noise | The noise the sensor's electronics add to every reading, even in the dark. |
| Readout scheme | The order and timing in which a sensor's pixels are exposed and read. |
| Reconstruction | Computing the picture of the surface from the recorded readings. |
| Redundancy | Measuring the same thing many times in different ways. It is what makes self-calibration and phase recovery possible. |
| Reference sample | An object whose pattern is already known from an independent measurement, used to check the instrument. |
| Reflectance | The share of incoming light that a point of the surface sends back. |
| Refractive index | The factor by which a material slows light. The wavelength inside the material is shorter by the same factor: 1.33 for water. |
| Registration | Working out how far one picture is shifted relative to another. |
| Regularisation | Adding a mild preference, such as smoothness, so that a reconstruction does not amplify noise into false detail. |
| Resolution | The finest detail that can be told apart. |
| Rolling shutter | A sensor that exposes and reads its rows one after another, so each row sees a slightly later moment. |
| Sample | One reading from one pixel at one moment. |
| Scatterometry | Measuring the dimensions of a regular pattern that is too fine to see, by fitting a model to how it reflects light at different colours and angles. |
| Self-calibration | Calibration done from the ordinary measurement data, with no separate test. |
| Sensor | The camera chip: a grid of pixels that turn light into electrical readings. |
| Shift and add | The simplest way to combine many frames: place every reading where its pixel was at that moment, and average the readings that land in the same place. |
| Signal-to-noise | How large the wanted signal is compared with the noise. Higher is better. |
| Sinc | The mathematical shape that describes how much of each detail size a box-shaped smear lets through. It falls steadily and touches zero at certain sizes. |
| Sparse | Made of few, well-separated features. |
| Spatial frequency | Fineness of detail, counted as repeats per unit length. One divided by the period. |
| Speckle | The grainy random pattern coherent light makes after passing through or bouncing off something rough. |
| Spectral width | The spread of wavelengths in a light source. A narrow spread means a pure colour and a long coherence length. |
| Stage | Used in two senses: a step of the staged path (stage 0 to stage 4), and the moving platform that carries a sample or the sensor. |
| Sub-pixel | Smaller than one pixel. |
| Super-resolution | Recovering detail finer than the pixels by combining many readings taken at slightly different positions. |
| Synthetic aperture | A large collecting opening built up by computation from many readings taken at different positions or angles. |
| Talbot effect | The reappearance of a sharp copy of a grating's pattern at set distances behind it when it is lit by a parallel beam of one colour. |
| Tile (patch) | A small square of the surface that is processed on its own, so that many can be processed at once. |
| Tilt | The small angle between the direction of the scan and the rows of the pixel grid. |
| Tolerance | How large an error in a quantity can be before the result is noticeably worse. |
| Transfer (transfer function) | For each size of detail, the share of its contrast that survives a stage of the instrument. 1 means untouched, 0 means lost. |
| Twin (simulated twin) | A simulation of a measurement procedure, run with known hidden values to show that the procedure recovers them before it is tried on hardware. |
| Ultraviolet | Light with a wavelength shorter than about 400 nm, which the eye cannot see. |
| View factor | The share of the light leaving one surface that lands directly on another, fixed by geometry alone. |
| Wavelength | The length of one cycle of a light wave: about 400 nm for violet, 550 nm for green, 650 nm for red. Light cannot easily carry detail finer than this. |
| Well conditioned | Said of a calculation in which small errors in the data cause only small errors in the answer. |
| Wiener filter | A standard way to undo a known blur that holds back where the noise would otherwise be amplified. |
