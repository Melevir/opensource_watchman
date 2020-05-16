import io
from typing import Optional

from requests import get
from requests.exceptions import MissingSchema
from PIL import Image


def get_image_height_in_pixels(url) -> Optional[int]:
    try:
        img_data = get(url).content
    except MissingSchema:
        return None
    im = Image.open(io.BytesIO(img_data))
    return im.size[1]
