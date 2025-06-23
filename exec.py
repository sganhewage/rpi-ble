import random

def game(val: str):
    #string is a list of comma separated values print each value
    values = val.split(',')
    for value in values:
        print(f"Value: {value.strip()}")

if __name__ == "__main__":
    game()