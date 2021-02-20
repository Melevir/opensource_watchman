import io
from typing import Optional

import deal
from requests import get
from requests.exceptions import MissingSchema
from PIL import Image


@deal.pre(lambda url: url.startswith('http'))
@deal.post(lambda r: r is None or r > 0)
def get_image_height_in_pixels(url: str) -> Optional[int]:
    try:
        img_data = get(url).content
    except MissingSchema:
        return None
    im = Image.open(io.BytesIO(img_data))
    return im.size[1]
