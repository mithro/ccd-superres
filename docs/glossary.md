# Glossary

Plain-language meanings of the terms used across this documentation. Pages
link here the first time they use a term that is not explained on the spot.

| Term | Meaning |
|---|---|
| Aperture | The opening through which light is collected. A wider opening, or a wider range of angles, lets finer detail through. |
| Approach | One complete way of building and running the instrument: a choice of light, optical parts, gap, sensor, readout, scan, exposure and reconstruction method. |
| Blur kernel | The shape that a single point of the surface is smeared into by the time it is recorded. A wide kernel means a blurry picture. |
| Coherent light | Light whose waves stay in step with each other, such as laser light. It can form interference patterns. Ordinary lamp light is not coherent. |
| Collection angle | The widest angle, away from straight ahead, at which a pixel still responds to light. |
| Contrast | How much brighter the bright parts of a pattern are than the dark parts. Blur lowers contrast. When it falls below the noise, the pattern is lost. |
| Convolution | The mathematical name for smearing: every point of a picture is replaced by a copy of the blur kernel, and the copies are added up. |
| Diffraction | The spreading of light into a fan of directions when it meets fine structure. Finer structure sends light out at steeper angles. |
| Diffuse (matt) surface | A surface that scatters light in all directions, like paper. The opposite is mirror-like. |
| Evanescent wave | Light that carries detail finer than the wavelength. It clings to the surface and fades within a fraction of a wavelength, so it never reaches a distant detector. |
| Exposure | The time during which a pixel adds up light for one reading. |
| Far field | Far enough from the surface, many wavelengths, that only ordinary travelling light is left. |
| Forward model | The calculation that predicts what the sensor would record for a given surface. Reconstruction runs it backwards. |
| Fourier ring correlation | A standard test of how fine the trustworthy detail in a reconstruction is, found by checking down to what size it still agrees with the truth or with a second independent reconstruction. |
| Frame | One complete readout of the sensor. |
| Fringes | The regular bright and dark stripes formed where two coherent beams overlap. |
| Gap | The distance between the light-sensitive layer of the sensor and the surface being examined. |
| Gate | The defined set of conditions a simulated approach must pass before any hardware is built for it. |
| Global shutter | A sensor in which every pixel is exposed at the same instant. See rolling shutter. |
| Inverse problem | Working out the cause from the effect: here, the surface from the recorded readings. |
| Lensless | With no lens between the surface and the sensor. |
| Line time | The time a sensor takes to read one row of pixels, 18.9 millionths of a second for the IMX219. |
| Mirror-like (specular) surface | A smooth surface that reflects light in one direction, like polished silicon. |
| Motion blur | Smearing caused by the sensor moving while a pixel is adding up light. |
| Near field | Within a fraction of a wavelength of the surface, where detail finer than the wavelength can still be picked up. |
| Noise | Random variation in the readings that does not come from the surface. Averaging many readings reduces it. |
| Period | The distance over which a regular pattern repeats. Lines and spaces each 100 nm wide have a period of 200 nm. |
| Phase | Where a wave is in its cycle. Sensors record brightness only, so phase has to be worked out by computation. |
| Phase recovery | Computing the lost phase of light from brightness readings taken under varied conditions. |
| Pixel pitch | The distance from the centre of one pixel to the next, 1.12 µm for the IMX219. |
| Pixel response | How strongly a pixel reacts to light depending on exactly where on the pixel it lands and from what angle it arrives. |
| Prior | Something assumed to be true about the surface before looking at the data, for example that chips have straight edges. |
| Ptychography | A method that scans a sample under coherent light, records many overlapping brightness patterns, and computes a sharp picture, including phase, from the overlap. |
| Read noise | The noise the sensor's electronics add to every reading, even in the dark. |
| Readout scheme | The order and timing in which a sensor's pixels are exposed and read. |
| Reconstruction | Computing the picture of the surface from the recorded readings. |
| Reflectance | The share of incoming light that a point of the surface sends back. |
| Regularisation | Adding a mild preference, such as smoothness, so that a reconstruction does not amplify noise into false detail. |
| Resolution | The finest detail that can be told apart. |
| Rolling shutter | A sensor that exposes and reads its rows one after another, so each row sees a slightly later moment. |
| Sample | One reading from one pixel at one moment. |
| Scatterometry | Measuring the dimensions of a regular pattern that is too fine to see, by fitting a model to how it reflects light at different colours and angles. |
| Signal-to-noise | How large the wanted signal is compared with the noise. Higher is better. |
| Sinc | The mathematical shape that describes how much of each detail size a box-shaped smear lets through. It falls steadily and touches zero at certain sizes. |
| Spatial frequency | Fineness of detail, counted as repeats per unit length. One divided by the period. |
| Speckle | The grainy random pattern coherent light makes after passing through or bouncing off something rough. |
| Sub-pixel | Smaller than one pixel. |
| Super-resolution | Recovering detail finer than the pixels by combining many readings taken at slightly different positions. |
| Synthetic aperture | A large collecting opening built up by computation from many readings taken at different positions or angles. |
| Tilt | The small angle between the direction of the scan and the rows of the pixel grid. |
| Transfer (transfer function) | For each size of detail, the share of its contrast that survives a stage of the instrument. 1 means untouched, 0 means lost. |
| Wavelength | The length of one cycle of a light wave: about 400 nm for violet, 550 nm for green, 650 nm for red. Light cannot easily carry detail finer than this. |
| Wiener filter | A standard way to undo a known blur that holds back where the noise would otherwise be amplified. |
