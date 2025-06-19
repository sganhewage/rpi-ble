import random

def game():
    correct_guesses = 0
    print("Guess the number between 1 and 5. Type 'exit' to quit.")

    while True:
        number = random.randint(1, 5)
        user_input = input("Your guess: ").strip()

        if user_input.lower() == 'exit':
            print(f"Game over! You guessed correctly {correct_guesses} times.")
            break

        if user_input.isdigit() and 1 <= int(user_input) <= 5:
            guess = int(user_input)
            if guess == number:
                print("Correct!")
                correct_guesses += 1
            else:
                print(f"Wrong! The number was {number}.")
        else:
            print(f"Game over! You guessed correctly {correct_guesses} times.")
            break

if __name__ == "__main__":
    game()