#  Copyright (c) 2024. L.J.Afres, All rights reserved.
import cv2


def grab(file):
    img = cv2.imread(file)
    _, b = cv2.pencilSketch(img, sigma_s=10, sigma_r=0.05, shade_factor=0.02)
    cv2.imwrite("output.png", b)
