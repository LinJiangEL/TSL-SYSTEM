#  Copyright (c) 2024. L.J.Afres, All rights reserved.

from pyzbar import pyzbar
from PIL import Image


def process(file):
    img = Image.open(file)
    img.convert("L")
    img.save(file)


def scan(file):
    results = []
    process(file)
    barcodes = pyzbar.decode(Image.open(file))
    for barcode in barcodes:
        results.append(barcode.data.decode("utf-8"))

    return results


# print(scan("2.png"))
scan("2.png")
