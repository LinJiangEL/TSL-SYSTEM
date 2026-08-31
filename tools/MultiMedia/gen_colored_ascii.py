#  Copyright (c) 2026. L.J.Afres, All rights reserved.

import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont

# ���������Ⱥ͸߶ȣ���/���أ�
output_width = 60
output_height = 35

# �����ɫ ASCII �ַ�����ͼ����������С
colored_ascii_image_font = "arialbd.ttf"
colored_ascii_image_font_size = 8

# �����ɫ ASCII �ַ����滻���ص� ASCII �ַ�
colored_ascii_chars = ["0", "1", "2", "3", "4", "5", "6", "8", "9"]

# ��ͼ�����Ϊָ����С
def resize_image(image_path, output_width, output_height):
    image = Image.open(image_path)
    image = image.resize((output_width, output_height))
    return image


# ��ͼ��ת��Ϊ�Ҷ�ͼ��
def convert_to_gray(image):    
    return image.convert('L')


# ��ͼ��ת��Ϊ��ɫ ASCII �ַ���
def image_to_colored_ascii(image_path, output_width, output_height):
    resized_image = resize_image(image_path, output_width, output_height)

    ascii_image = []
    ascii_image_chars = []
    ascii_image_colors=[]
    for y in range(output_height):
        row = ""
        for x in range(output_width):
            color = resized_image.getpixel((x, y))

            gray_value = sum(color) // 3
            char_index = int(gray_value / 255 * (len(colored_ascii_chars) - 1))
            if char_index >= len(colored_ascii_chars):
                char_index = len(colored_ascii_chars) - 1

            row += f"\033[38;2;{color[0]};{color[1]};{color[2]}m{colored_ascii_chars[char_index]}"

            ascii_image_chars.append(colored_ascii_chars[char_index])
            ascii_image_colors.append((color[0], color[1], color[2]))

        ascii_image.append(row)

    return "\n".join(ascii_image), ascii_image_chars, ascii_image_colors


# ����ɫ ASCII ����ͼ��洢ΪͼƬ
def save_colored_ascii_image_as_picture(ascii_image_chars, ascii_image_colors, font_path, font_size, output_path):
    image = Image.new('RGB', ((output_width * font_size), (output_height * font_size)), color='black')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    for i in range(output_height):
        for j in range(output_width):
            draw.text((j * font_size, i * font_size), ascii_image_chars[i*output_width+j], font=font, fill=ascii_image_colors[i*output_width+j])

    image.save(output_path)

if __name__ == "__main__":
    image_path = "path/to/your/image.jpg"

    # ��ͼ��ת��Ϊ��ɫ ASCII �ַ���
    colored_ascii_image, colored_ascii_image_chars, colored_ascii_image_colors = image_to_colored_ascii(image_path, output_width, output_height)

    # �洢��ɫ ASCII �ַ�����ͼƬ�ļ�
    save_colored_ascii_image_as_picture(colored_ascii_image_chars, colored_ascii_image_colors, colored_ascii_image_font, colored_ascii_image_font_size, "colored_ascii_image.png")

    # ���ն˴��ڴ�ӡ��ɫ ASCII �ַ���
    print(colored_ascii_image)
