# Supa-Converter

**Supa-Converter is a free, open-source desktop image converter for Windows and Python users.** Convert images in batches, compress them with adjustable quality settings, preview the results, and export everything in one ZIP archive. Files are processed locally on your computer—no account, subscription, or image upload required.

Need an easy-to-use app? Download the ready-to-run Windows `.exe` from the project’s **GitHub Releases** once the executable is published. Prefer Python? Run the source code directly.

## Why use Supa-Converter?

- **Batch image conversion:** Add multiple images and convert them together.
- **Popular output formats:** Export as **WEBP, JPEG/JPG, PNG, GIF, TIFF, or BMP**.
- **Adjustable compression and quality:** Tune the setting and preview the encoded result before exporting. The effect depends on the selected format.
- **Side-by-side preview:** Compare the original image with its converted output, including the resulting file size.
- **One-click batch package:** Save successfully converted images together in a ZIP file.
- **Private, local processing:** Images are read and converted on your device; Supa-Converter does not upload them to a conversion service.
- **Free and open source:** Use the Python application without a paid plan or online account.
- **Optional standalone Windows app:** Use the `.exe` release without installing Python or setting up a development environment.

Supa-Converter is built for quick, straightforward everyday image conversion and compression. Actual processing time and output size depend on your computer, image dimensions, source format, and selected settings.

## Download the Windows app

When available, download the latest Supa-Converter `.exe` from the **Assets** section of the project’s [GitHub Releases](https://github.com/SupaTx/Supa-Converter/releases). The executable is intended for people who want to use the graphical app without installing Python or its dependencies.

> The executable will be added as a release asset. Until then, use the Python instructions below.

## Run from Python

### Requirements

- Python 3
- Pillow
- Tkinter, which is included with many Python installations (some Linux distributions package it separately)

### Install and launch

1. Clone or download this repository.
2. Open a terminal in the project directory.
3. Install Pillow and start the app:

```bash
python -m pip install Pillow
python main.py
```

On systems where Python is invoked as `python3`, use:

```bash
python3 -m pip install Pillow
python3 main.py
```

## Convert and compress images

1. Launch Supa-Converter.
2. Select **Add Images** and choose one or more files.
3. Choose an output format: WEBP, JPEG, PNG, GIF, TIFF, or BMP.
4. Adjust the **Compression / Quality** slider when it is available. The app updates the preview when you change the format or setting.
5. Select an image in the queue to view the original and converted preview, with the output size and size difference.
6. Select **Preview Batch Processing** to process the queued images.
7. Select **Save Converted Batch (.zip)** and choose where to save the ZIP archive.

Converted files are named after their source files, with `_supa` added before the extension. If names would collide, Supa-Converter adds a number to keep each file distinct. Files that fail to process are reported in the queue; successfully processed images can still be exported.

## Output formats and quality settings

| Format | Notes |
| --- | --- |
| **WEBP** | Modern format with adjustable quality and compression. |
| **JPEG / JPG** | Adjustable quality; images with transparency are composited onto a dark background because JPEG does not support transparency. |
| **PNG** | Lossless encoding with an adjustable compression effort. The slider changes compression settings, not a promise of smaller files. |
| **GIF** | The quality setting controls the output color palette. Animated-image preservation is not currently supported; images are loaded as a single frame. |
| **TIFF** | Saved with LZW compression; the quality slider is inactive. |
| **BMP** | Saved as a bitmap; the quality slider is inactive. |

Supa-Converter does **not** promise that every conversion will reduce file size or preserve identical visual quality. Lossless formats such as PNG preserve image data through encoding, while JPEG, WEBP, and GIF settings may trade visual fidelity for smaller files. Always inspect the preview and output that suit your needs.

## Build a standalone Windows executable

You can package the Python application as a Windows executable with [PyInstaller](https://pyinstaller.org/). From the project directory, install the build tool and run:

```bash
python -m pip install Pillow pyinstaller
python -m PyInstaller --onefile --windowed --name Supa-Converter main.py
```

The executable will be created in the `dist` directory. Build the Windows `.exe` on Windows. The build tool is only needed to create an executable; it is not required to run the Python source.

## Privacy

Supa-Converter processes selected images locally using Python and Pillow. It does not need an internet connection to convert images, and the application code does not upload your images to a remote conversion service.

## Troubleshooting

- **The app does not open:** Confirm Python 3 and Pillow are installed, then run `python main.py` from a terminal to see any error message.
- **Tkinter is missing:** Install the Tkinter package provided for your operating system or Python distribution.
- **A file cannot be converted:** The input must be readable by the installed Pillow build. Some formats may require additional system support; try another image or format.
- **The converted image is larger:** This can happen depending on the source, output format, dimensions, and quality settings. Compare the preview sizes and try a different format or setting.
- **Transparency looks different in JPEG:** JPEG has no transparency support. Supa-Converter composites transparent areas onto a dark background for JPEG output.

## Technology

Supa-Converter is a Python desktop application built with **Tkinter** for its graphical interface and **Pillow** for image loading, previewing, format conversion, and encoding. Image EXIF orientation is applied when loading images.

## Contributing and support

Bug reports, feature suggestions, and contributions are welcome. Please open an issue in this repository with steps to reproduce a problem and, when possible, details about your operating system, Python version, input format, and selected output settings. Avoid attaching private or sensitive images.

## License

Supa-Converter is open-source software. See the [LICENSE](LICENSE) file for the applicable license terms.

---

**Search topics:** free image converter for Windows, batch image converter, compress images offline, convert PNG to WEBP, convert JPG to PNG, Python image conversion app, local image compressor, open-source image converter, image converter EXE.
