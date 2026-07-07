import exifread
from pathlib import Path
from PIL import Image, ExifTags

class MetadataReader:
    def __init__(self):
        self._cache = {}

    def get_metadata(self, path: Path):
        if path in self._cache:
            return self._cache[path]
        metadata = {}
        try:
            with open(path, "rb") as f:
                tags = exifread.process_file(f, details=False)
            for tag, value in tags.items():
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                    metadata[tag] = str(value)
        except Exception:
            # fallback to PIL
            try:
                img = Image.open(path)
                exifdata = img.getexif()
                for tag_id, value in exifdata.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    metadata[tag_name] = str(value)
            except Exception:
                pass
        self._cache[path] = metadata
        return metadata