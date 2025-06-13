#!/usr/bin/env python3
"""
Raw Contact Sheet Generator - Modern Command Line Version
Updated for Python 3 and modern macOS compatibility
"""

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps
from PIL import ImageFilter

import sys
import os
import subprocess
from io import BytesIO
import time
import argparse

class ContactSheetGenerator(object):
    def __init__(self, directory_in="", config=None):
        self.contactSheetConfiguration = {
            "directoryIn": directory_in,
            "directoryOut": "",
            "contactSheetWidth": 600,
            "panelInfo": False,
            "histogramInfo": False,
            "histogramAlpha": 128,
            "histogramWidth": 255,
            "histogramHeight": 100,
            "expandPercent": 5,
            "fontColor": "#ff9c00",
            "useEmbeddedJpg": False,
            "expandHistogram": False,
            "sharpen": True,
            "sharpenAmount": 1,
            "format": ["jpg", "tiff", "ppm"],
            "bitDepth": [8],
            "JPG_Quality": 95,
            "dcrawOption_extractJPG": [False],
            "dcrawOption_half": [True],
            "dcrawOption_quality": [True, 0],
            "dcrawOption_dontStretchRotatePixels": [True],
            "dcrawOption_whiteBalance": ["w"],
            "style": ["single", "strip", "grid"],
            "stripLength": 4,
            "gridSize": [2, 5]
        }

        if config:
            self.contactSheetConfiguration.update(config)

        self.catchCanonExifTags = {
            "EXIF_camera": "Exif.Image.Model",
            "EXIF_make": "Exif.Image.Make",
            "EXIF_Date": "Exif.Image.DateTime",
            "EXIF_shutter": "Exif.Photo.ExposureTime",
            "EXIF_author": "Exif.Image.Artist",
            "EXIF_aperture": "Exif.Photo.FNumber",
            "EXIF_shootingMode": "Exif.Photo.ExposureProgram",
            "EXIF_ISO": "Exif.Photo.ISOSpeedRatings",
            "EXIF_compensation": "Exif.Photo.ExposureBiasValue",
            "EXIF_meteringMode": "Exif.Photo.MeteringMode",
            "EXIF_focalLength": "Exif.Photo.FocalLength",
            "EXIF_fileFormat": "Exif.CanonCs.Quality",
            "EXIF_lens": "Exif.Canon.LensModel",
            "EXIF_fileColorSpace": "Exif.Canon.ColorSpace",
            "EXIF_whiteBalance": "Exif.CanonPr.ColorTemperature",
            "EXIF_fileResolutionWidth": "Exif.Image.ImageWidth",
            "EXIF_fileResolutionHeight": "Exif.Image.ImageHeight"
        }

        self.ExifTags = {
            "customText": "NEF|Nikon"
        }

        self.ExifTagsPositions = {
            "customText": ["panel", 0],
            "EXIF_camera": ["top", 0],
            "EXIF_make": ["panel", 0],
            "EXIF_Date": ["panel", 0],
            "EXIF_shutter": ["top", 0],
            "EXIF_author": ["panel", 0],
            "EXIF_aperture": ["top", 0],
            "EXIF_shootingMode": ["panel", 60],
            "EXIF_ISO": ["top", 0],
            "EXIF_compensation": ["panel", 0],
            "EXIF_meteringMode": ["panel", 0],
            "EXIF_focalLength": ["panel", 0],
            "EXIF_fileFormat": ["panel", 0],
            "EXIF_lens": ["panel", 50],
            "EXIF_fileColorSpace": ["panel", 0],
            "EXIF_whiteBalance": ["panel", 0],
            "EXIF_fileResolutionWidth": ["panel", 0],
            "EXIF_fileResolutionHeight": ["panel", 0]
        }

        self.ExifTagsShow = {
            "customText": False,
            "EXIF_camera": True,
            "EXIF_make": True,
            "EXIF_Date": True,
            "EXIF_shutter": True,
            "EXIF_author": True,
            "EXIF_aperture": True,
            "EXIF_shootingMode": True,
            "EXIF_ISO": True,
            "EXIF_compensation": True,
            "EXIF_meteringMode": True,
            "EXIF_focalLength": True,
            "EXIF_fileFormat": True,
            "EXIF_lens": True,
            "EXIF_fileColorSpace": True,
            "EXIF_whiteBalance": True,
            "EXIF_fileResolutionWidth": True,
            "EXIF_fileResolutionHeight": True
        }

        self.fileList = []
        self.imageWidth = 0
        self.imageHeight = 0
        self.imageExpandedHeight = 0
        self.imageExpandedWidth = 0
        self.imageMargin = 20
        self.textPadding = 15  # Consistent padding between EXIF elements
        self.actualCropWidth = 0  # Store actual crop width used
        self.actualCropHeight = 0  # Store actual crop height used
        self.actualBottomMargin = 0  # Store actual bottom margin used

        if directory_in:
            self.getImagesFromDirectory(directory_in)
            self.processFiles()

    def processFiles(self):
        print("Processing files:")
        for fileName in self.fileList:
            t0 = time.time()
            print(f"Processing: {os.path.basename(fileName)}")
            self.extractShootingInformation(fileName)
            image = self.makeThumb(fileName)
            self.saveImage(image, fileName)
            t1 = time.time()
            print(f"{fileName} done in {t1-t0:.2f} seconds")

    def saveImage(self, image, filePath):
        fileName, fileExtension = os.path.splitext(filePath)
        fileName = fileName + "_cs.jpg"
        quality_val = self.contactSheetConfiguration["JPG_Quality"]
        image.save(fileName, 'JPEG', quality=quality_val)
        print(f"Saved: {fileName}")

    def getImagesFromDirectory(self, directory):
        path = directory
        extensionTypes = [".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2", ".pef", ".srw", ".jpg", ".tiff", ".tif"]

        if os.path.isfile(path):
            # Single file provided
            self.fileList.append(path)
            return

        fileList = os.listdir(path)
        fileList = [f.lower() for f in fileList]

        print("Files found - will overwrite previously generated contactSheets:")
        for fileName in fileList:
            for ext_type in extensionTypes:
                if fileName.endswith(ext_type):
                    if not os.path.splitext(fileName)[0].endswith("_cs"):
                        fileName = os.path.join(path, fileName)
                        # Find original case filename
                        orig_files = os.listdir(path)
                        for orig_file in orig_files:
                            if orig_file.lower() == os.path.basename(fileName).lower():
                                fileName = os.path.join(path, orig_file)
                                break
                        self.fileList.append(fileName)
                    else:
                        print(f"---overwrite warning: {fileName}")

        print("Files to process:")
        for f in self.fileList:
            print(f"  {f}")

    def imageCanvasExpand(self, image, percent):
        # Calculate base margin from the larger dimension
        if image.size[0] > image.size[1]:
            baseMargin = (image.size[0] // 100) * percent
        else:
            baseMargin = (image.size[1] // 100) * percent

        # Calculate minimum space needed for text
        fontsize = self.contactSheetConfiguration["contactSheetWidth"] // 12
        fontScale = 0.3
        text_height = int(fontsize * fontScale * 1.4)  # 1.4x for padding (reduced from 1.5x)
        min_text_space = text_height + 15  # Text height + comfortable padding (reduced from 20)

        # All margins are reduced by half
        topMargin = baseMargin // 2
        sideMargin = baseMargin // 2
        bottomMargin = baseMargin // 2

        # If text won't fit in top margin, scale image down to make room
        scale_factor = 1.0
        if topMargin < min_text_space:
            # Calculate how much we need to scale the image
            # We want: topMargin + scaled_image_height + bottomMargin = original_canvas_height
            # But with enough topMargin for text
            needed_reduction = min_text_space - topMargin
            scale_factor = 1.0 - (needed_reduction / image.size[1])
            scale_factor = max(scale_factor, 0.9)  # Don't scale below 90%

            # Scale the image
            scaled_width = int(image.size[0] * scale_factor)
            scaled_height = int(image.size[1] * scale_factor)
            image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

            # Recalculate margins based on scaled image to maintain proportions
            if image.size[0] > image.size[1]:
                baseMargin = (image.size[0] // 100) * percent
            else:
                baseMargin = (image.size[1] // 100) * percent

            topMargin = max(baseMargin // 2, min_text_space)
            sideMargin = baseMargin // 2
            bottomMargin = baseMargin // 2

        # Store the actual crop dimensions for text positioning
        self.actualCropWidth = sideMargin
        self.actualCropHeight = topMargin
        self.actualBottomMargin = bottomMargin

        # Create new image with expanded canvas
        new_width = image.size[0] + 2 * sideMargin
        new_height = image.size[1] + topMargin + bottomMargin
        expanded = Image.new('RGB', (new_width, new_height), 'black')
        expanded.paste(image, (sideMargin, topMargin))

        self.imageExpandedWidth = expanded.size[0]
        self.imageExpandedHeight = expanded.size[1]
        return expanded

    def imageSharpen(self, image, amount):
        return image.filter(ImageFilter.SHARPEN)

    def extractShootingInformation(self, imagePath):
        # Use exiv2 instead of exiv2.exe for macOS
        exiv2_opts = ["exiv2", "-p", "a", imagePath]
        try:
            result = subprocess.run(exiv2_opts, capture_output=True, text=True, timeout=30)
            rawExif = result.stdout
            rawExifLines = rawExif.split("\n")

            for line in rawExifLines:
                for key in self.catchCanonExifTags.keys():
                    if self.catchCanonExifTags[key] in line:
                        self.ExifTags[key] = line.split("  ")[-1].rstrip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            print(f"Warning: Could not extract EXIF data from {imagePath}")

    def imageGenerateSpreadText(self, image, text_string, image_width):
        if not text_string:
            return image

        fontColor = self.contactSheetConfiguration["fontColor"]
        fontsize = self.contactSheetConfiguration["contactSheetWidth"] // 12
        fontScale = 0.3

        # Try to find Iosvmata font or fallback to system fonts
        font_paths = [
            "/System/Library/Fonts/Iosvmata.ttf",
            "/Library/Fonts/Iosvmata.ttf",
            "/usr/local/share/fonts/Iosvmata.ttf",
            "/opt/homebrew/share/fonts/Iosvmata.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Monaco.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ]

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, fontsize)
                    break
                except OSError:
                    continue

        if not font:
            font = ImageFont.load_default()

        # Use the stored actual crop dimensions from canvas expansion
        cropWidth = self.actualCropWidth
        cropHeight = self.actualCropHeight

        # The image frame starts at (cropWidth, cropHeight) after expansion
        # Align text with the left edge of the image frame
        image_left_edge = cropWidth

        # Create text image for the entire string
        try:
            bbox = font.getbbox(text_string)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback for older PIL versions
            text_width, text_height = font.getsize(text_string)

        # Add padding to prevent clipping
        padding = fontsize // 2
        textImage = Image.new('RGBA', (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0))
        textImageDraw = ImageDraw.Draw(textImage)
        textImageDraw.text((padding, padding), text_string, font=font, fill=fontColor)

        textImage = textImage.resize((int(textImage.size[0] * fontScale),
                                     int(textImage.size[1] * fontScale)),
                                    Image.Resampling.LANCZOS)

        # Calculate vertical offset
        padding = 6  # Padding between text bottom and image top
        vertOffset = cropHeight - textImage.size[1] - padding + 2  # Move down by 2px

        # Make sure text doesn't go above the top edge
        if vertOffset < 2:
            vertOffset = 2  # Minimum 2px from top edge

        # Left-aligned positioning with slight offset
        horOffset = image_left_edge - 4

        image.paste(textImage, (int(horOffset), int(vertOffset)), textImage)

        return image

    def imageWriteExif(self, image, fileName, original_width=None):
        # Create single line with: Camera, ISO, shutter, aperture, filename
        top_line_parts = []

        # Camera
        if self.ExifTagsShow.get("EXIF_camera", False) and "EXIF_camera" in self.ExifTags:
            top_line_parts.append(self.ExifTags["EXIF_camera"])

        # ISO
        if self.ExifTagsShow.get("EXIF_ISO", False) and "EXIF_ISO" in self.ExifTags:
            iso_text = self.ExifTags["EXIF_ISO"]
            if not iso_text.startswith("ISO"):
                iso_text = f"ISO {iso_text}"
            top_line_parts.append(iso_text)

        # Shutter speed
        if self.ExifTagsShow.get("EXIF_shutter", False) and "EXIF_shutter" in self.ExifTags:
            shutter_text = self.ExifTags["EXIF_shutter"]
            if "/" in shutter_text and not shutter_text.endswith("s"):
                shutter_text = f"{shutter_text}s"
            top_line_parts.append(shutter_text)

        # Aperture
        if self.ExifTagsShow.get("EXIF_aperture", False) and "EXIF_aperture" in self.ExifTags:
            aperture_text = self.ExifTags["EXIF_aperture"]
            # Remove f/ prefix if it exists, then add f/
            if aperture_text.startswith("f/F"):
                aperture_text = aperture_text[3:]  # Remove "f/F"
            elif aperture_text.startswith("f/"):
                aperture_text = aperture_text[2:]  # Remove "f/"
            elif aperture_text.startswith("F"):
                aperture_text = aperture_text[1:]  # Remove "F"
            aperture_text = f"f/{aperture_text}"
            top_line_parts.append(aperture_text)

        # Filename
        import os
        filename = os.path.basename(fileName)
        top_line_parts.append(filename)

        # Create single text string with spacing
        if top_line_parts:
            # Join all parts with consistent spacing
            text_string = "    ".join(top_line_parts)  # 4 spaces between elements
            # Use original width if provided, otherwise fall back to stored width
            width_to_use = original_width if original_width is not None else self.imageWidth
            image = self.imageGenerateSpreadText(image, text_string, width_to_use)

        return image

    def imageHistogram(self, image):
        histogramImage = Image.new('RGBA', (255, 100), (0, 0, 0, 0))
        hist = image.histogram()

        histogramImageR = hist[0:256]
        histogramImageG = hist[256:512]
        histogramImageB = hist[512:768]

        histogramImageMax = [max(histogramImageR), max(histogramImageG), max(histogramImageB)]
        histogramImageMaxL = max(histogramImageMax)

        if histogramImageMaxL == 0:
            return histogramImage

        histogramImageDraw = ImageDraw.Draw(histogramImage)

        for i in range(min(255, len(histogramImageR))):
            r_height = int((histogramImageR[i] / histogramImageMaxL) * 100)
            g_height = int((histogramImageG[i] / histogramImageMaxL) * 100)
            b_height = int((histogramImageB[i] / histogramImageMaxL) * 100)

            histogramImageDraw.line([(i, 0), (i, r_height)], fill="#FF0000")
            histogramImageDraw.line([(i, 0), (i, g_height)], fill="#00FF00")
            histogramImageDraw.line([(i, 0), (i, b_height)], fill="#0000FF")

        histogramImage = histogramImage.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        return histogramImage

    def pasteHistogram(self, image, imageHistogram):
        imageHistogram.putalpha(self.contactSheetConfiguration["histogramAlpha"])

        imageHistogramWidth = self.contactSheetConfiguration["histogramWidth"]
        imageHistogramHeight = self.contactSheetConfiguration["histogramHeight"]
        imageHistogram = imageHistogram.resize((imageHistogramWidth, imageHistogramHeight))

        paste_x = (image.size[0] - imageHistogram.size[0]) - self.actualCropWidth
        paste_y = (image.size[1] - imageHistogram.size[1]) - self.actualBottomMargin

        image.paste(imageHistogram, (paste_x, paste_y), imageHistogram)
        return image

    def imageResize(self, image):
        self.imageWidth = image.size[0]
        self.imageHeight = image.size[1]

        imageRatio = image.size[1] / float(image.size[0])

        if image.size[0] < image.size[1]:
            self.imageHeight = self.contactSheetConfiguration["contactSheetWidth"]
            self.imageWidth = int(self.imageHeight / imageRatio)
        else:
            self.imageWidth = self.contactSheetConfiguration["contactSheetWidth"]
            self.imageHeight = int((image.size[1] * self.imageWidth) // image.size[0])

        image = image.resize((self.imageWidth, self.imageHeight), Image.Resampling.LANCZOS)
        return image

    def makeThumb(self, file):
        expandPercent = self.contactSheetConfiguration["expandPercent"]
        sharpenAmount = self.contactSheetConfiguration["sharpenAmount"]

        if file.lower().endswith((".jpg", ".jpeg")):
            image = Image.open(file)
        elif file.lower().endswith((".tif", ".tiff")):
            # Extract from TIFF using dcraw
            dcraw_opts = ["dcraw", "-c", "-4", "-T", file]
            print(f"Running: {' '.join(dcraw_opts)}")
            try:
                result = subprocess.run(dcraw_opts, capture_output=True, timeout=60)
                if result.returncode == 0:
                    rawImage = BytesIO(result.stdout)
                    image = Image.open(rawImage)
                else:
                    # Fallback to direct PIL open
                    image = Image.open(file)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                print(f"dcraw failed for {file}, trying direct open")
                image = Image.open(file)
        elif file.lower().endswith((".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2", ".pef", ".srw")):
            # Extract from RAW using dcraw
            dcraw_opts = ["dcraw", "-c", file]
            print(f"Running: {' '.join(dcraw_opts)}")
            try:
                result = subprocess.run(dcraw_opts, capture_output=True, timeout=60)
                if result.returncode == 0:
                    rawImage = BytesIO(result.stdout)
                    image = Image.open(rawImage)
                else:
                    raise Exception(f"dcraw failed with return code {result.returncode}")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
                print(f"Error processing RAW file {file}: {e}")
                # Create a placeholder image
                image = Image.new('RGB', (800, 600), 'gray')
                draw = ImageDraw.Draw(image)
                draw.text((50, 300), f"Error processing:\n{os.path.basename(file)}", fill='white')
        else:
            try:
                image = Image.open(file)
            except Exception as e:
                print(f"Error opening {file}: {e}")
                image = Image.new('RGB', (800, 600), 'gray')

        # Rotate portrait images to landscape orientation
        if image.size[1] > image.size[0]:  # Height > Width = Portrait
            image = image.rotate(90, expand=True)
            print(f"Rotated portrait image to landscape: {os.path.basename(file)}")

        # Generate histogram before resizing
        imageHistogram = self.imageHistogram(image)

        # Resize image
        image = self.imageResize(image)

        # Calculate margin
        if image.size[0] > image.size[1]:
            self.imageMargin = (image.size[0] // 100) * self.contactSheetConfiguration["expandPercent"]
        else:
            self.imageMargin = (image.size[1] // 100) * self.contactSheetConfiguration["expandPercent"]

        # Store original image dimensions before expansion
        self.imageWidth = image.size[0]
        self.imageHeight = image.size[1]

        # Apply effects
        if self.contactSheetConfiguration["expandHistogram"]:
            image = ImageOps.autocontrast(image)

        if self.contactSheetConfiguration["sharpen"]:
            image = self.imageSharpen(image, sharpenAmount)

        # Store dimensions before expansion (in case image gets scaled)
        pre_expansion_width = image.size[0]

        image = self.imageCanvasExpand(image, expandPercent)
        image = self.imageWriteExif(image, file, pre_expansion_width)

        if self.contactSheetConfiguration["histogramInfo"]:
            image = self.pasteHistogram(image, imageHistogram)

        return image

def main():
    parser = argparse.ArgumentParser(description='Generate contact sheets from RAW and image files')
    parser.add_argument('input', help='Input directory or file')
    parser.add_argument('-w', '--width', type=int, default=600, help='Contact sheet width (default: 600)')
    parser.add_argument('-q', '--quality', type=int, default=95, help='JPEG quality (default: 95)')
    parser.add_argument('--histogram', action='store_true', help='Enable histogram overlay')
    parser.add_argument('--custom-text', action='store_true', help='Enable custom text overlay')
    parser.add_argument('--no-exif', action='store_true', help='Disable EXIF information display')
    parser.add_argument('--no-sharpen', action='store_true', help='Disable image sharpening')

    args = parser.parse_args()

    # Configure settings
    config = {
        'contactSheetWidth': args.width,
        'JPG_Quality': args.quality,
        'histogramInfo': args.histogram,
        'sharpen': not args.no_sharpen
    }

    # Handle custom text
    if not args.custom_text:
        config['ExifTagsShow'] = {'customText': False}

    # Disable EXIF if requested
    if args.no_exif:
        config['ExifTagsShow'] = {key: False for key in config.get('ExifTagsShow', {})}

    # Check if dcraw and exiv2 are available
    for tool in ['dcraw', 'exiv2']:
        try:
            if tool == 'dcraw':
                result = subprocess.run([tool], capture_output=True, text=True, timeout=5)
                if 'dcraw' not in result.stdout:
                    print(f"Warning: {tool} not found or not working properly")
            else:
                subprocess.run([tool, '--version'], capture_output=True, check=True, timeout=5)
            print(f"✓ {tool} is available")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"✗ {tool} not found. Install with: brew install {tool}")
            if tool == 'dcraw':
                print("  dcraw is required for RAW file processing")
                return 1

    print(f"\nProcessing: {args.input}")
    print(f"Settings: Width={args.width}, Quality={args.quality}, Histogram={args.histogram}")

    # Create generator and process
    try:
        generator = ContactSheetGenerator(args.input, config)
        print("\nDone!")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
