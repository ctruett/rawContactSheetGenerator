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
from datetime import datetime
from io import BytesIO
import time
import argparse
import math

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
            "EXIF_CaptureDate": "Exif.Photo.DateTimeOriginal",
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
            "EXIF_CaptureDate": ["panel", 0],
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
            "EXIF_CaptureDate": True,
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
        self.frameCounter = 0  # Frame counter for folder processing
        self.isProcessingFolder = False  # Track if processing a folder
        self.htmlImages = []  # Store image info for HTML generation
        self.contactSheetImages = []  # Store processed images for contact sheet generation

        if directory_in:
            self.getImagesFromDirectory(directory_in)
            self.processFiles()

    def processFiles(self):
        print("Processing files:")
        # Set folder processing flag if we have multiple files
        self.isProcessingFolder = len(self.fileList) > 1
        self.frameCounter = 0

        for fileName in self.fileList:
            t0 = time.time()
            if self.isProcessingFolder or self.contactSheetConfiguration.get('renameFrames', False):
                self.frameCounter += 1
            print(f"Processing: {os.path.basename(fileName)}")

            self.extractShootingInformation(fileName)
            image = self.makeThumb(fileName)

            # Store image for contact sheet generation if requested
            if self.contactSheetConfiguration.get('generateContactSheet', False):
                self.contactSheetImages.append({
                    'image': image.copy(),
                    'filename': os.path.basename(fileName),
                    'filepath': fileName
                })
                # Skip saving individual images when generating contact sheet
                print(f"Stored image for contact sheet: {os.path.basename(fileName)}")
            else:
                self.saveImage(image, fileName)

            # Export 2000px version if requested
            if self.contactSheetConfiguration.get('export2000px', False):
                self.export2000pxVersion(fileName)

            t1 = time.time()
            print(f"{fileName} done in {t1-t0:.2f} seconds")

        # Generate HTML contact sheet if requested
        if self.contactSheetConfiguration.get('generateHTML', False):
            print(f"HTML generation enabled, calling generateHTMLContactSheet()")
            self.generateHTMLContactSheet()
        else:
            print(f"HTML generation disabled (generateHTML: {self.contactSheetConfiguration.get('generateHTML', 'not set')})")

        # Generate PNG contact sheet if requested
        if self.contactSheetConfiguration.get('generateContactSheet', False):
            print(f"PNG contact sheet generation enabled, calling generatePNGContactSheet()")
            self.generatePNGContactSheet()
        else:
            print(f"PNG contact sheet generation disabled (generateContactSheet: {self.contactSheetConfiguration.get('generateContactSheet', 'not set')})")

    def saveImage(self, image, filePath):
        # Create date-gallery subfolder
        dir_path = os.path.dirname(filePath)

        # Get date from EXIF for folder name
        folder_date = ""
        if hasattr(self, 'ExifTags') and 'EXIF_CaptureDate' in self.ExifTags and self.ExifTags['EXIF_CaptureDate']:
            try:
                from datetime import datetime
                date_str = self.ExifTags['EXIF_CaptureDate']
                date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                folder_date = date_obj.strftime('%Y-%m-%d')
            except:
                pass

        if not folder_date:
            from datetime import datetime
            folder_date = datetime.now().strftime('%Y-%m-%d')

        # Create folder name: YYYY-MM-DD Gallery Name
        gallery_name = self.contactSheetConfiguration.get('galleryName', 'Contact Sheet')
        folder_name = f"{folder_date} {gallery_name}"
        gallery_dir = os.path.join(dir_path, folder_name)
        if not os.path.exists(gallery_dir):
            os.makedirs(gallery_dir)
            print(f"Created directory: {gallery_dir}")

        # Determine output filename
        base_name = os.path.basename(filePath)
        if self.contactSheetConfiguration.get('renameFrames', False) and self.frameCounter > 0:
            # Use frame number as filename
            fileName = os.path.join(gallery_dir, f"{self.frameCounter:03d}_cs.jpg")
        else:
            # Use original filename
            fileName, fileExtension = os.path.splitext(base_name)
            fileName = os.path.join(gallery_dir, fileName + "_cs.jpg")

        quality_val = self.contactSheetConfiguration["JPG_Quality"]
        image.save(fileName, 'JPEG', quality=quality_val)
        print(f"Saved: {fileName}")

        # Store image info for HTML generation
        if self.contactSheetConfiguration.get('generateHTML', False):
            self.htmlImages.append({
                'filename': os.path.basename(fileName),
                'path': fileName,
                'frame': self.frameCounter if self.frameCounter > 0 else None,
                'exif': dict(self.ExifTags) if hasattr(self, 'ExifTags') else {}
            })
            print(f"Added image to HTML list: {os.path.basename(fileName)}")





    def generatePNGContactSheet(self):
        """Generate a single PNG contact sheet with all processed images"""
        if not self.contactSheetImages:
            print("No images available for contact sheet generation")
            return

        print(f"Creating contact sheet with {len(self.contactSheetImages)} images")

        # Calculate grid dimensions
        num_images = len(self.contactSheetImages)
        if num_images == 1:
            cols, rows = 1, 1
        elif num_images <= 4:
            cols, rows = 2, 2
        elif num_images <= 9:
            cols, rows = 3, 3
        elif num_images <= 16:
            cols, rows = 4, 4
        elif num_images <= 25:
            cols, rows = 5, 5
        else:
            # For larger numbers, use a rectangular grid
            cols = int(math.ceil(math.sqrt(num_images * 1.5)))
            rows = int(math.ceil(num_images / cols))

        # Get dimensions of first image to calculate contact sheet size
        first_image = self.contactSheetImages[0]['image']
        img_width, img_height = first_image.size

        # Calculate contact sheet dimensions with padding
        padding = 20
        contact_width = cols * img_width + (cols + 1) * padding
        contact_height = rows * img_height + (rows + 1) * padding

        # Create blank contact sheet
        contact_sheet = Image.new('RGB', (contact_width, contact_height), 'black')

        # Paste images into contact sheet
        for i, img_data in enumerate(self.contactSheetImages):
            if i >= cols * rows:  # Don't exceed grid capacity
                break

            row = i // cols
            col = i % cols

            x = col * img_width + (col + 1) * padding
            y = row * img_height + (row + 1) * padding

            # Paste the image
            contact_sheet.paste(img_data['image'], (x, y))

            print(f"Placed image {i+1}/{len(self.contactSheetImages)}: {img_data['filename']}")

        # Save contact sheet in input folder
        dir_path = os.path.dirname(self.contactSheetImages[0]['filepath'])

        # Save as PNG directly in input folder
        contact_sheet_path = os.path.join(dir_path, "contact-sheet.png")
        contact_sheet.save(contact_sheet_path, 'PNG')
        print(f"Contact sheet saved: {contact_sheet_path}")
        print(f"Contact sheet dimensions: {contact_width}x{contact_height} pixels")
        print(f"Grid layout: {cols}x{rows} images")



    def generateHTMLContactSheet(self):
        """Generate an HTML contact sheet with all processed images and lightbox functionality"""
        print(f"Starting HTML generation with {len(self.htmlImages)} images")

        # Create date-gallery folder if it doesn't exist
        if self.fileList:
            dir_path = os.path.dirname(self.fileList[0])

            # Determine the date for folder name from EXIF capture date
            dates = []
            for img_info in self.htmlImages:
                # Try to extract date from EXIF capture date
                if 'EXIF_CaptureDate' in img_info['exif'] and img_info['exif']['EXIF_CaptureDate']:
                    try:
                        from datetime import datetime
                        date_str = img_info['exif']['EXIF_CaptureDate']
                        # EXIF date format: YYYY:MM:DD HH:MM:SS
                        date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        dates.append(date_obj)
                    except:
                        pass

            # Use the first date found, or fallback to today
            if dates:
                dates.sort()
                folder_date = dates[0].strftime('%Y-%m-%d')
            else:
                from datetime import datetime
                folder_date = datetime.now().strftime('%Y-%m-%d')

            # Create folder name: YYYY-MM-DD Gallery Name
            gallery_name = self.contactSheetConfiguration.get('galleryName', 'Contact Sheet')
            folder_name = f"{folder_date} {gallery_name}"
            gallery_dir = os.path.join(dir_path, folder_name)
            if not os.path.exists(gallery_dir):
                os.makedirs(gallery_dir)

            # Generate HTML content
            gallery_name = self.contactSheetConfiguration.get('galleryName', 'Contact Sheet')
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + gallery_name + """</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #000000;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #ffffff;
            margin-bottom: 30px;
        }
        .grid {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        .image-container {
            cursor: pointer;
            border: 2px solid transparent;
            transition: border-color 0.2s;
        }
        .image-container:hover {
            border-color: #666666;
        }
        .image-container img {
            display: block;
            max-width: 100%;
            height: auto;
        }
        .date-range {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .timestamp {
            text-align: center;
            color: #666;
            margin-top: 30px;
            font-size: 0.9em;
        }

        /* Lightbox styles */
        .lightbox {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
            cursor: pointer;
        }
        .lightbox-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        }
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 35px;
            color: #fff;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
        }
        .lightbox-close:hover {
            color: #ff9c00;
        }
        .lightbox-nav {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            color: #fff;
            font-size: 30px;
            font-weight: bold;
            cursor: pointer;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 10px 15px;
            border-radius: 5px;
            user-select: none;
        }
        .lightbox-nav:hover {
            color: #ff9c00;
            background-color: rgba(0, 0, 0, 0.8);
        }
        .lightbox-prev {
            left: 20px;
        }
        .lightbox-next {
            right: 20px;
        }

    </style>
</head>
<body>
    <div class="container">
        <h1>""" + gallery_name + """</h1>
        <div class="date-range" id="date-range"></div>
        <div class="grid">
"""

            # Determine date range for display (reuse dates extracted above)
            date_range_str = ""
            if dates:
                start_date = dates[0]
                end_date = dates[-1]

                if start_date.date() == end_date.date():
                    # Single date
                    date_range_str = start_date.strftime("%B %d, %Y")
                else:
                    # Date range
                    if start_date.year == end_date.year:
                        if start_date.month == end_date.month:
                            # Same month
                            date_range_str = f"{start_date.strftime('%B %d')} - {end_date.strftime('%d, %Y')}"
                        else:
                            # Same year, different months
                            date_range_str = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
                    else:
                        # Different years
                        date_range_str = f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"

            # Add each image to the HTML
            for i, img_info in enumerate(self.htmlImages):
                # Use relative path for images
                img_path = os.path.basename(img_info['path'])

                # Determine the large image path (without _cs suffix)
                large_img_path = img_path.replace('_cs.jpg', '.jpg')

                html_content += f"""
            <div class="image-container" onclick="openLightbox({i})">
                <img src="{img_path}" alt="Image {i+1}" loading="lazy">
            </div>
"""

            # Add lightbox HTML and JavaScript
            from datetime import datetime
            timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            html_content += f"""
        </div>
        <div class="timestamp">Generated on {timestamp}</div>
    </div>

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox" onclick="closeLightbox()">
        <span class="lightbox-close" onclick="closeLightbox()">&times;</span>
        <div class="lightbox-nav lightbox-prev" onclick="event.stopPropagation(); previousImage()">&#10094;</div>
        <div class="lightbox-nav lightbox-next" onclick="event.stopPropagation(); nextImage()">&#10095;</div>
        <img class="lightbox-content" id="lightbox-image" onclick="event.stopPropagation();">

    </div>

    <script>
        // Image data for lightbox
        const images = ["""

            # Add image data for JavaScript
            for i, img_info in enumerate(self.htmlImages):
                large_img_path = img_info['path'].replace('_cs.jpg', '.jpg')
                large_img_path = os.path.basename(large_img_path)

                if i > 0:
                    html_content += ","
                html_content += f"""
            {{
                src: "{large_img_path}"
            }}"""

            html_content += """
        ];

        let currentImageIndex = 0;

        function openLightbox(index) {
            currentImageIndex = index;
            const lightbox = document.getElementById('lightbox');
            const lightboxImage = document.getElementById('lightbox-image');

            lightboxImage.src = images[index].src;

            lightbox.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }

        function closeLightbox() {
            document.getElementById('lightbox').style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        function nextImage() {
            currentImageIndex = (currentImageIndex + 1) % images.length;
            openLightbox(currentImageIndex);
        }

        function previousImage() {
            currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
            openLightbox(currentImageIndex);
        }

        // Keyboard navigation
        document.addEventListener('keydown', function(event) {
            const lightbox = document.getElementById('lightbox');
            if (lightbox.style.display === 'block') {
                switch(event.key) {
                    case 'Escape':
                        closeLightbox();
                        break;
                    case 'ArrowRight':
                        nextImage();
                        break;
                    case 'ArrowLeft':
                        previousImage();
                        break;
                }
            }
        });

        // Set date range
        const dateRangeElement = document.getElementById('date-range');
        const dateRange = '""" + date_range_str + """';
        if (dateRange) {
            dateRangeElement.textContent = dateRange;
        }
    </script>
</body>
</html>
"""

            # Write HTML file
            html_path = os.path.join(gallery_dir, "index.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"\nGenerated HTML gallery: {html_path}")
        else:
            print("No images found for HTML generation")

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
                        pass

        # Sort files alphabetically for consistent frame numbering
        self.fileList.sort()

        print("\nFiles to process:")
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

        # If text won't fit in margins, scale image down to make room
        scale_factor = 1.0
        # Check if either top or bottom margin needs more space
        if topMargin < min_text_space or bottomMargin < min_text_space:
            # Calculate how much we need to scale the image
            # We need enough space in both top and bottom margins
            needed_top = max(0, min_text_space - topMargin)
            needed_bottom = max(0, min_text_space - bottomMargin)
            needed_reduction = max(needed_top, needed_bottom)
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
            bottomMargin = max(baseMargin // 2, min_text_space)

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

    def imageGenerateSpreadText(self, image, text_string, image_width, position="top", align="left"):
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
        bottomMargin = self.actualBottomMargin

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

        # Calculate vertical offset based on position
        if position == "top":
            padding = 6  # Padding between text bottom and image top
            vertOffset = cropHeight - textImage.size[1] - padding + 1  # Move down by 2px

            # Make sure text doesn't go above the top edge
            if vertOffset < 2:
                vertOffset = 2  # Minimum 2px from top edge
        else:  # bottom
            # Position text in bottom margin
            # Calculate where the image bottom is
            # Total height - bottom margin = where image ends
            image_bottom = image.size[1] - bottomMargin
            padding = 6  # Padding between image bottom and text top
            vertOffset = image_bottom + padding - 3  # Move up by 3px

        # Positioning based on alignment
        if align == "right":
            # Right-aligned positioning - align to right edge of image frame
            horOffset = image_left_edge + image_width - textImage.size[0] - 22
        else:
            # Left-aligned positioning with slight offset
            horOffset = image_left_edge - 7

        image.paste(textImage, (int(horOffset), int(vertOffset)), textImage)

        return image

    def export2000pxVersion(self, filePath):
        """Export a 2000px wide version of the original image"""
        try:
            # Open the original file
            if filePath.lower().endswith((".jpg", ".jpeg")):
                image = Image.open(filePath)
            elif filePath.lower().endswith((".tif", ".tiff")):
                # Try to open TIFF directly first
                try:
                    image = Image.open(filePath)
                except:
                    # Fall back to dcraw for TIFF if needed
                    dcraw_opts = ["dcraw", "-c", "-4", "-T", filePath]
                    result = subprocess.run(dcraw_opts, capture_output=True, timeout=60)
                    if result.returncode == 0:
                        rawImage = BytesIO(result.stdout)
                        image = Image.open(rawImage)
                    else:
                        raise Exception("Failed to process TIFF")
            else:
                # RAW file - use dcraw
                dcraw_opts = ["dcraw", "-c", filePath]
                result = subprocess.run(dcraw_opts, capture_output=True, timeout=60)
                if result.returncode == 0:
                    rawImage = BytesIO(result.stdout)
                    image = Image.open(rawImage)
                else:
                    raise Exception("Failed to process RAW file")

            # Calculate new size (max 2000px wide)
            if image.size[0] > 2000:
                ratio = 2000.0 / image.size[0]
                new_height = int(image.size[1] * ratio)
                image = image.resize((2000, new_height), Image.Resampling.LANCZOS)

            # Apply sharpening after resize
            # Use less aggressive sharpening than contact sheets since these are larger
            sharpen_filter = ImageFilter.UnsharpMask(radius=1, percent=100, threshold=3)
            image = image.filter(sharpen_filter)

            # Create gallery subfolder
            dir_path = os.path.dirname(filePath)

            # Get date from EXIF for folder name
            folder_date = ""
            if hasattr(self, 'ExifTags') and 'EXIF_CaptureDate' in self.ExifTags and self.ExifTags['EXIF_CaptureDate']:
                try:
                    from datetime import datetime
                    date_str = self.ExifTags['EXIF_CaptureDate']
                    date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    folder_date = date_obj.strftime('%Y-%m-%d')
                except:
                    pass

            if not folder_date:
                from datetime import datetime
                folder_date = datetime.now().strftime('%Y-%m-%d')

            # Create folder name: YYYY-MM-DD Gallery Name
            gallery_name = self.contactSheetConfiguration.get('galleryName', 'Contact Sheet')
            folder_name = f"{folder_date} {gallery_name}"
            gallery_dir = os.path.join(dir_path, folder_name)
            if not os.path.exists(gallery_dir):
                os.makedirs(gallery_dir)

            # Determine output filename
            base_name = os.path.basename(filePath)
            if self.contactSheetConfiguration.get('renameFrames', False) and self.frameCounter > 0:
                # Use frame number as filename
                output_name = os.path.join(gallery_dir, f"{self.frameCounter:03d}.jpg")
            else:
                # Use original filename
                name_only, ext = os.path.splitext(base_name)
                output_name = os.path.join(gallery_dir, f"{name_only}.jpg")

            # Convert RGBA to RGB if necessary for JPEG
            if image.mode == 'RGBA':
                # Create a white background and paste the image on it
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                image = rgb_image

            # Save with high quality
            image.save(output_name, 'JPEG', quality=95)
            print(f"Exported 2000px version: {output_name}")

        except Exception as e:
            print(f"Error exporting 2000px version of {filePath}: {e}")

    def imageWriteExif(self, image, fileName, original_width=None):
        # Put date or filename at top
        import os
        top_text = ""

        if self.contactSheetConfiguration.get('showFilename', False):
            # Show filename if flag is set
            top_text = os.path.basename(fileName)
        else:
            # Show date by default - try capture date first, then regular date
            date_str = None
            if self.ExifTags.get("EXIF_CaptureDate"):
                date_str = self.ExifTags["EXIF_CaptureDate"]
            elif self.ExifTags.get("EXIF_Date"):
                date_str = self.ExifTags["EXIF_Date"]

            if date_str:
                # Format date nicely (YYYY:MM:DD HH:MM:SS -> May 6th, 2025)
                try:
                    # Parse the EXIF date format
                    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")

                    # Get ordinal suffix for day
                    day = dt.day
                    if 11 <= day <= 13:
                        suffix = 'th'
                    else:
                        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

                    # Format as "May 6th, 2025"
                    top_text = dt.strftime(f"%B {day}{suffix}, %Y")
                except:
                    # Fallback to original date string if parsing fails
                    top_text = date_str
            else:
                # Fallback to filename if no date available
                top_text = os.path.basename(fileName)

        if top_text:
            width_to_use = original_width if original_width is not None else self.imageWidth
            image = self.imageGenerateSpreadText(image, top_text, width_to_use, position="top")

        # Add frame counter in top right if processing folder, or date if in PNG contact sheet mode
        if self.isProcessingFolder and self.frameCounter > 0:
            if self.contactSheetConfiguration.get('generateContactSheet', False):
                # Show formatted date in top right for PNG contact sheet mode
                date_str = None
                if self.ExifTags.get("EXIF_CaptureDate"):
                    date_str = self.ExifTags["EXIF_CaptureDate"]
                elif self.ExifTags.get("EXIF_Date"):
                    date_str = self.ExifTags["EXIF_Date"]

                if date_str:
                    try:
                        # Parse the EXIF date format
                        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        # Get ordinal suffix for day
                        day = dt.day
                        if 11 <= day <= 13:
                            suffix = 'th'
                        else:
                            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                        # Format as "May 6th, 2025"
                        date_text = dt.strftime(f"%B {day}{suffix}, %Y")
                    except:
                        # Fallback to original date string if parsing fails
                        date_text = date_str

                    width_to_use = original_width if original_width is not None else self.imageWidth
                    image = self.imageGenerateSpreadText(image, date_text, width_to_use, position="top", align="right")
            else:
                # Show frame counter for normal mode
                frame_text = f"{self.frameCounter:03d}"
                width_to_use = original_width if original_width is not None else self.imageWidth
                image = self.imageGenerateSpreadText(image, frame_text, width_to_use, position="top", align="right")

        # Create EXIF info for bottom: Camera, ISO, shutter, aperture
        bottom_line_parts = []

        # Camera
        if self.ExifTagsShow.get("EXIF_camera", False) and "EXIF_camera" in self.ExifTags:
            bottom_line_parts.append(self.ExifTags["EXIF_camera"])

        # ISO
        if self.ExifTagsShow.get("EXIF_ISO", False) and "EXIF_ISO" in self.ExifTags:
            iso_text = self.ExifTags["EXIF_ISO"]
            if not iso_text.startswith("ISO"):
                iso_text = f"ISO {iso_text}"
            bottom_line_parts.append(iso_text)

        # Shutter speed
        if self.ExifTagsShow.get("EXIF_shutter", False) and "EXIF_shutter" in self.ExifTags:
            shutter_text = self.ExifTags["EXIF_shutter"]
            if "/" in shutter_text and not shutter_text.endswith("s"):
                shutter_text = f"{shutter_text}s"
            bottom_line_parts.append(shutter_text)

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
            bottom_line_parts.append(aperture_text)

        # Create single text string with spacing for bottom line
        if bottom_line_parts:
            # Join all parts with consistent spacing
            text_string = "    ".join(bottom_line_parts)  # 4 spaces between elements
            # Use original width if provided, otherwise fall back to stored width
            width_to_use = original_width if original_width is not None else self.imageWidth
            image = self.imageGenerateSpreadText(image, text_string, width_to_use, position="bottom")

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
    parser.add_argument('--show-filename', action='store_true', help='Show filename instead of date at top of image')
    parser.add_argument('--rename', action='store_true', help='Rename output files to frame numbers')
    parser.add_argument('--export', action='store_true', help='Export 2000px wide JPEGs of input files')
    parser.add_argument('--html', action='store_true', help='Generate HTML contact sheet with lightbox (automatically enables --export)')
    parser.add_argument('--png', action='store_true', help='Generate a single PNG contact sheet image with all frames')

    parser.add_argument('--gallery-name', type=str, default='Contact Sheet', help='Name for the HTML gallery (default: Contact Sheet)')

    args = parser.parse_args()

    # Automatically enable export and rename when HTML is requested (for lightbox functionality)
    if args.html:
        args.export = True
        args.rename = True
        print("HTML generation enabled - automatically enabling --export and --rename for lightbox functionality")

    # Automatically enable show-filename when PNG contact sheet is requested
    if args.png:
        args.show_filename = True
        print("PNG contact sheet generation enabled - automatically enabling --show-filename")

    # Configure settings
    config = {
        'contactSheetWidth': args.width,
        'JPG_Quality': args.quality,
        'histogramInfo': args.histogram,
        'sharpen': not args.no_sharpen,
        'showFilename': args.show_filename,
        'renameFrames': args.rename,
        'export2000px': args.export,
        'generateHTML': args.html,
        'generateContactSheet': args.png,
        'galleryName': args.gallery_name
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
    print(f"Settings: Width={args.width}, Quality={args.quality}, Histogram={args.histogram}, ContactSheet={args.png}")

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
