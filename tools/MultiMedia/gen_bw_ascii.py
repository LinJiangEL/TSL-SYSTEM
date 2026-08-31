#  Copyright (c) 2026. L.J.Afres, All rights reserved.

import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont

# 定义输出宽度和高度（行/像素）
output_width = 60
output_height = 35

# 定义黑白 ASCII 字符画绘图字体和字体大小
bw_ascii_image_font = "arial.ttf"
bw_ascii_image_font_size = 8

# 定义黑白 ASCII 字符画替换像素的 ASCII 字符
bw_ascii_chars = "@%#*+=-:. "

# 将图像调整为指定大小
def resize_image(image_path, output_width, output_height):
    image = Image.open(image_path)
    image = image.resize((output_width, output_height))
    return image

# 将图像转换为灰度图像
def convert_to_gray(image):    
    return image.convert('L')

# 将像素映射为 ASCII 字符
def map_pixels_to_ascii(gray_image, ascii_chars):
    ascii_image = []

    for y in range(output_height):
        row = ""
        for x in range(output_width):
            gray_value = gray_image.getpixel((x, y))
            char_index = int(gray_value / 255 * (len(ascii_chars) - 1))
            row += ascii_chars[char_index]
        ascii_image.append(row)

    return "\n".join(ascii_image)


# 将图像转换为黑白 ASCII 字符画
def image_to_bw_ascii(image_path, output_width, output_height):
    resized_image = resize_image(image_path, output_width, output_height)

    gray_image = convert_to_gray(resized_image)    

    ascii_image = map_pixels_to_ascii(gray_image, bw_ascii_chars)

    return ascii_image


# 存储黑白 ASCII 字符画到文本文件
def save_bw_ascii_image_as_text(ascii_image, output_path):
    with open(output_path, 'w') as file:
        file.write(ascii_image)


# 存储黑白 ASCII 字符画到图片
def save_bw_ascii_image_as_picture(ascii_image, font_path, font_size, output_path):
    lines = ascii_image.split('\n')
    width = max(len(line) for line in lines)
    height = len(lines)

    image = Image.new('RGB', ((width * font_size), height * font_size), color='white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            draw.text((x * font_size, y * font_size), char, font=font, fill='black')

    image.save(output_path)


if __name__ == "__main__":
    image_path = "MeowMeow.png"

    # 生成黑白 ASCII 字符画
    bw_ascii_image = image_to_bw_ascii(image_path, output_width, output_height)

    # 存储黑白 ASCII 字符画到文本文件
    save_bw_ascii_image_as_text(bw_ascii_image, "bw_ascii_image.txt")

    # 存储黑白 ASCII 字符画到图片文件
    save_bw_ascii_image_as_picture(bw_ascii_image, bw_ascii_image_font, bw_ascii_image_font_size, "bw_ascii_image.png")

    # 在终端窗口打印彩色 ASCII 字符画
    print(bw_ascii_image)