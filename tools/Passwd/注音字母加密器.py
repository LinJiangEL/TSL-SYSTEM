def encrypt_message(message):
    nato_alphabet = {
        'A': 'Alfa', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta',
        'E': 'Echo', 'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel',
        'I': 'India', 'J': 'Juliet', 'K': 'Kilo', 'L': 'Lima',
        'M': 'Mike', 'N': 'November', 'O': 'Oscar', 'P': 'Papa',
        'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango',
        'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'Xray',
        'Y': 'Yankee', 'Z': 'Zulu'
    }

    encrypted_message = ""

    # 对消息中的字母进行迭代
    for letter in message:
        # 如果字典中有该字母，则将对应的值添加到加密信息中
        if letter.upper() in nato_alphabet:
            encrypted_message += nato_alphabet[letter.upper()] + " "

        # 如果字典中有该字母，则将该字母添加到加密信息中
        else:
            encrypted_message += letter

    return encrypted_message


message = "Hello World"
encrypted_message = encrypt_message(message)
print("Encrypted message: ", encrypted_message)
