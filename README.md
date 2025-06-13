# Raw Contact Sheet Generator

A Python tool for creating professional contact sheets from RAW images and standard image formats. Displays EXIF metadata, supports batch processing, and offers customizable output options.

## Features

- **Wide Format Support**: Process RAW files (CR2, CR3, NEF, ARW, DNG, RAF, ORF, RW2, PEF, SRW) and standard formats (JPEG, TIFF, PPM)
- **EXIF Display**: Shows camera model, ISO, shutter speed, aperture, and photo date/time
- **Batch Processing**: Process entire directories of images with automatic frame numbering
- **Auto-Rotation**: Automatically rotates portrait images to landscape
- **Image Enhancement**: Optional sharpening and auto-contrast
- **Histogram Overlay**: Display RGB histogram on contact sheets
- **Optimized Layout**: Compact margins with well-positioned metadata text
- **Organized Output**: All output files are saved to a `cs` subfolder
- **Export Options**: Generate 2000px wide JPEGs alongside contact sheets

## Requirements

- Python 3.6+
- PIL/Pillow
- pyexiv2
- dcraw (for RAW processing)

## Installation

1. Clone the repository:
```bash
git clone git@github.com:ctruett/rawContactSheetGenerator.git
cd rawContactSheetGenerator
```

2. Install Python dependencies:
```bash
pip install Pillow pyexiv2
```

3. Install dcraw:
   - macOS: `brew install dcraw`
   - Linux: `sudo apt-get install dcraw`
   - Windows: Download dcraw.exe and place in project directory

## Usage

Basic usage:
```bash
python contactSheetGenerator_modern_cli.py /path/to/images
```

With options:
```bash
# Set output width to 800px with 90% JPEG quality
python contactSheetGenerator_modern_cli.py -w 800 -q 90 /path/to/images

# Enable histogram overlay
python contactSheetGenerator_modern_cli.py --histogram /path/to/images

# Disable sharpening
python contactSheetGenerator_modern_cli.py --no-sharpen /path/to/images
```

## Command Line Options

- `-w, --width`: Contact sheet width in pixels (default: 600)
- `-q, --quality`: JPEG output quality 1-100 (default: 95)
- `--histogram`: Enable RGB histogram overlay
- `--no-exif`: Disable EXIF information display
- `--no-sharpen`: Disable automatic sharpening
- `--custom-text`: Enable custom text overlay
- `--show-filename`: Show filename instead of photo date at top of image
- `--rename`: Rename output files to frame numbers (001.jpg, 002.jpg, etc.)
- `--export`: Export 2000px wide JPEGs of input files in addition to contact sheets

## Output

All output files are saved in a `cs` subfolder within the source directory:
- Contact sheets: `cs/IMG_1234_cs.jpg`
- 2000px exports: `cs/IMG_1234.jpg` (with `--export`)
- Frame-numbered: `cs/001_cs.jpg`, `cs/001.jpg` (with `--rename`)

## License

MIT License - see LICENSE file for details