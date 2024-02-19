import os
import json
import sys
from random import randrange
from random import randint


class Pet (object):
    """A virtual pet"""
    pet_type = None
    exicitement_reduce = 3
    exicitement_max = 10
    exicitement_warning = 3
    food_reduce = 2
    food_max = 10
    food_warning = 3
    

    def __init__(self, name, animal_type):
        self.name = name
        self.animal_type = animal_type
        self.food = randint(2,self.food_max)
        self.exicitement = randint(2,self.exicitement_max)


    def __clock_tick(self):
        self.exicitement -= 1
        self.food -= 1

    def mood(self):
        if self.exicitement > 0 and self.food > 0:
            if self.food > self.food_warning and self.exicitement > self.exicitement_warning:
                return "happy"
            elif self.food < self.food_warning:
                return "hungry"
            else:
                return "bored"
        else:
            print('Your pet died')
        
    def __str__(self):
        if self.exicitement > 0 and self.food > 0:
            return "\n I'm " + self.name + "." + "\n I feel " + self.mood() + "."
        else:
            print("Your pet died...")


    def talk(self):
        if self.exicitement > 0 and self.food > 0:
            print("I am a " + self.animal_type + ", named " + self.name + ". I feel " + self.mood() + " now.\n")
            self.__clock_tick()
        else:
            print("Your pet died...")

    def feed(self):
        if self.exicitement > 0 and self.food > 0:
            print("***crunch*** \n mmm. Thank you!"+str(self.food))
            meal = randrange(self.food, self.food_max)
            self.food += meal
            if self.food > self.food_max:
                self.food = self.food_max
            self.__clock_tick()
        else:
            print("Your pet died...")

    def play(self):
        if self.exicitement > 0 and self.food > 0:
            print("Woohoo!"+str(self.exicitement))
            fun = randrange(self.exicitement, self.exicitement_max)
            self.exicitement += fun
            if self.exicitement > self.exicitement_max:
                self.exicitement = self.exicitement_max
            self.__clock_tick()
        else:
            print("Your pet died...") 
    
    def return_state(self):
        if self.exicitement > 0 and self.food > 0:
            return True
        else:
            return False
        
    def get_state(self):
        return {
            'name': self.name,
            'animal_type': self.animal_type,
            'food': self.food,
            'exicitement': self.exicitement,
        }

def save_game(pet):
    with open('pet_game_save.json', 'w') as f:
        json.dump(pet.get_state(), f)
    print("Game saved successfully.")
    
def load_game():
    try:
        with open('pet_game_save.json', 'r') as f:
            data = json.load(f)
        pet = Pet(data['name'], data['animal_type'])
        pet.food = data['food']
        pet.exicitement = data['exicitement']
        return pet
    except FileNotFoundError:
        return None
    
def delete_saved_game():
    try:
        os.remove('pet_game_save.json')
        print("Saved game deleted successfully.")
    except FileNotFoundError:
        print("No saved game file found.")
    
def main():
    my_pet = load_game()
    if my_pet is None:
        pet_name = input("What do you want to name your pet? ")
        pet_type = None
        while pet_type != "dog" or pet_type != "cat" or pet_type != "owl":
            pet_type = input("Choose between *DOG* *CAT* *OWL* : ").lower()
            if pet_type == "dog" or pet_type == "cat" or pet_type == "owl":
                break
        my_pet = Pet(pet_name, pet_type)
        input("Hello! I am " + my_pet.name + " and I am new here! Press enter to start.")
        pass
    else:
        print(f"Welcome back, {my_pet.name}!")
    pet_type = my_pet.animal_type
    x = 3
    vocab_owl = ['"Hooo, hoo..."','"Buuuh, buuuh..."','"hello"','"hi"']
    vocab_dog = ['"Grrr..."','"Wuf! Wuf!"','"hello"','"hi"']
    vocab_cat = ['"meeooow..."', '"kjjjj!"','"hello"','"hi"']
    choice = None
    while choice != 0:
        print(
"""

*** INTERACT WITH YOUR PET ***

    1 - Feed your pet
    2 - Talk with your pet
    3 - Teach your pet a new word
    4 - Play with your pet
    5 - Save the game
    6 - Delete saved game
    0 - Quit
"""     
)  
        choice = input("Choice: ")

        if choice == "0":
            choice2 = None
            while choice2 != "y" or choice2 != "n":
                choice2 = input("Are you sure you want to leave ? y/n (Don't forget to save the game.) ").lower()
                if choice2 == "n":
                    break
                if choice2 == "y":
                    exit_program()

        elif choice == "1":
            my_pet.feed()

        elif choice == "2":
            my_pet.talk()
            if my_pet.return_state() == True:
                if pet_type == "dog":
                    print(vocab_dog[randint(0,x)])
                elif pet_type == "cat":
                    print(vocab_cat[randint(0,x)])
                elif pet_type == "owl":
                    print(vocab_owl[randint(0,x)])

        elif choice == "3":
            new_word = input("What do you want to teach your pet to say? ")
            x += 1
            if pet_type == "dog":
                vocab_dog.append('"' + new_word + '"')
            elif pet_type == "cat":
                vocab_cat.append('"' + new_word + '"')
            elif pet_type == "owl":
                vocab_owl.append('"' + new_word + '"')

        elif choice == "4":
            my_pet.play()

        elif choice == "5":
            save_game(my_pet)

        elif choice == "6":
            delete_saved_game()

        else:
            print("Sorry, that isn't a valid option.")

def exit_program():
    print("Exiting the game...")
    sys.exit(0)

if __name__ == "__main__":
    
    main()