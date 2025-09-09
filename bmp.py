def load(file_path) -> (int, int, bytearray):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            offset = int.from_bytes(content[10:14], 'little') 
            width = int.from_bytes(content[18:22], 'little')
            height = int.from_bytes(content[22:26], 'little')
            img_data = bytearray(content[offset:])
            return (width, height, img_data)
    except FileExistsError:
        print(f"Error: the file `{file_path}` was not found")
    pass