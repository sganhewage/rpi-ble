import random

def game(val: str):
    #string is a list of comma separated values print each value
    values = val.split(',')
    for value in values:
        print(f"Value: {value.strip()}")
    print(f"Length of values: {len(values)}")

if __name__ == "__main__":
    game()