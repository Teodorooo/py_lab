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
    state = None
    

    def __init__(self, name, animal_type):
        self.name = name
        self.animal_type = animal_type
        self.food = randrange(self.food_max)
        self.exicitement = randrange(self.exicitement_max)
        self.state = True


    def __clock_tick(self):
        self.exicitement -= 1
        self.food -= 1

    def mood(self):
        if self.state == True:
            if self.food > self.food_warning and self.exicitement > self.exicitement_warning:
                return "happy"
            elif self.food < self.food_warning:
                return "hungry"
            else:
                return "bored"
        else:
            print('Your pet died')
        
    def __str__(self):
        if self.state == True:
            return "\n I'm " + self.name + "." + "\n I feel " + self.mood() + "."
        else:
            print("Your pet died...")


    def talk(self):
        if self.state == True:
            print("I am a " + self.animal_type + ", named " + self.name + ". I feel " + self.mood() + " now.\n")
            self.__clock_tick()
        else:
            print("Your pet died...")

    def feed(self):
        if self.state == True:
            print("***crunch*** \n mmm. Thank you!"+str(self.food))
            meal = randrange(self.food, self.food_max)
            self.food += meal
            if self.food < 0:
                self.state = False

            elif self.food > self.food_max:
                self.food = self.food_max
            self.__clock_tick()
        else:
            print("Your pet died...")

    def play(self):
        if self.state == True:
            print("Woohoo!"+str(self.exicitement))
            fun = randrange(self.exicitement, self.exicitement_max)
            self.exicitement += fun
            if self.exicitement < 0:
                self.state = False
            elif self.exicitement > self.exicitement_max:
                self.exicitement = self.exicitement_max
            self.__clock_tick
        else:
            print("Your pet died...") 

    def return_state(self):     
        return self.state    

def main():
    x = 3
    vocab_owl = ['"Hooo, hoo..."','"Buuuh, buuuh..."','"hello"','"hi"']
    vocab_dog = ['"Grrr..."','"Wuf! Wuf!"','"hello"','"hi"']
    vocab_cat = ['"meeooow..."', '"kjjjj!"','"hello"','"hi"']
    pet_name = input("What do you want to name your pet? ")
    pet_type = None
    while pet_type != "dog" or pet_type != "cat" or pet_type != "owl":
        pet_type = input("Choose between *DOG* *CAT* *OWL* : ").lower()
        if pet_type == "dog" or pet_type == "cat" or pet_type == "owl":
            break
    my_pet = Pet(pet_name, pet_type)
    return_state = Pet(pet_name, pet_type).return_state() 
    input("Hello! I am " + my_pet.name + " and I am new here! Press enter to start.")
    choice = None
    while choice != 0:
        print(
"""

***INTERACT WITH YOUR PET***
    1 - Feed your pet
    2 - Talk with your pet
    3 - Teach your pet a new word
    4 - Play wth your pet
    0 - Quit
"""     
)  
        choice = input("Choice: ")
        if choice == "0":
            choice2 = None
            while choice2 != "y" or choice2 != "n":
                choice2 = input("Are you sure you want to leave ? y/n (The game will not save)").lower()
                if choice2 == "n":
                    break
                if choice2 == "y":
                    exit_program()
        elif choice == "1":
            my_pet.feed()
            print(return_state)
        elif choice == "2" and pet_type == "dog" and return_state == True:
            my_pet.talk()
            print(vocab_dog[randint(0,x)])
        elif choice == "2" and pet_type == "cat" and return_state == True:
            my_pet.talk()
            print(vocab_cat[randint(0,x)])
        elif choice == "2" and pet_type == "owl" and return_state == True:
            my_pet.talk()
            print(vocab_owl[randint(0,x)])
        elif choice == "3" and pet_type == "dog":
            x += 1
            new_word = input("What do you want to teach your pet to say? ")
            vocab_dog.append('"' + new_word + '"')
        elif choice == "3" and pet_type == "cat":
            x += 1
            new_word = input("What do you want to teach your pet to say? ")
            vocab_cat.append('"' + new_word + '"')
        elif choice == "3" and pet_type == "owl":
            x += 1
            new_word = input("What do you want to teach your pet to say? ")
            vocab_owl.append('"' + new_word + '"')
        elif choice == "4":
            my_pet.play()
        else:
            print("Sorry, that isn't a valid option.")

def exit_program():
    print("Teminating the game...")
    sys.exit(0)

if __name__ == "__main__":


    main()
