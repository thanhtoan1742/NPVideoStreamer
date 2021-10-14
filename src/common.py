def log(message: str, header: str = ""):
    print("-"*60)
    if header != "":
        print(header)
        print("-"*40)
    print(message)
    print("-"*60)
