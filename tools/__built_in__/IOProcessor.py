from ast import literal_eval

patterns = ['username','password','terminal']

class InputProcessor:
    def __init__(self):
        self.patterns_username = list(range())

    def illegal_match(self, text, pattern):
        if pattern in patterns:
            chars = [ichar for ichar in text.split() if ichar not in ['\n']]
            for char in chars:
                if ord(char) in literal_eval(f"self.patterns_{pattern}"):
                    return False
                else:
                    return True
        else:
            print(f"NameError:pattern '{pattern}' is not defined in patterns.")
         
