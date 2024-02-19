import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel
import os
import json
import sys
import random
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
    hygene_reduce = 2
    hygene_max = 10
    hygene_warning = 3  

    def __init__(self, name, animal_type):
        self.vocab_owl = ['"Hooo, hoo..."', '"Buuuh, buuuh..."', '"hello"', '"hi"']
        self.vocab_dog = ['"Grrr..."', '"Wuf! Wuf!"', '"hello"', '"hi"']
        self.vocab_cat = ['"meeooow..."', '"kjjjj!"', '"hello"', '"hi"']
        y = randint(1,3)
        self.name = name
        self.animal_type = animal_type
        if y == 1:
            self.food = 2
            self.exicitement = randint(4,self.exicitement_max)
            self.hygene = randint(4,self.hygene_max)
        elif y == 2:
            self.exicitement = 2
            self.food = randint(4,self.food_max)
            self.hygene = randint(4,self.hygene_max)
        else:
            self.hygene = 2
            self.food = randint(4,self.food_max)
            self.exicitement = randint(4,self.exicitement_max)

    def teach(self, new_word):
        self.new_word = new_word
        if self.animal_type == "dog":
            self.vocab_dog.append('"' + self.new_word + '"')
        elif self.animal_type == "cat":
            self.vocab_cat.append('"' + self.new_word + '"')
        else:
            self.vocab_owl.append('"' + self.new_word + '"')
           
    def clock_tick(self):
        self.exicitement -= 1
        self.food -= 1
        self.hygene -= 1

    def return_state(self):
        if self.exicitement > 0 and self.food > 0 and self.hygene > 0:
            return "Alive"
        else:
            return "Dead"
        
    def mood(self):
        if self.food > self.food_warning and self.exicitement > self.exicitement_warning and self.hygene > self.exicitement_warning:
            return "happy"
        elif self.food < self.food_warning:
            return "hungry"
        elif self.hygene < self.hygene_warning:
            return "filthy"
        else:
            return "bored"        

    def talk(self):
        if self.return_state() == "Alive":
            print("I am a " + self.animal_type + ", named " + self.name + ". I feel " + self.mood() + " now.\n")
            if self.animal_type == "dog":
                print(randrange(self.vocab_dog))
            elif self.animal_type == "cat":
                print(randrange(self.vocab_cat))
            else:
                print(randrange(self.vocab_owl))
            self.clock_tick()
        else:
            print("Your pet died...")

    def feed(self):
        if self.return_state() == "Alive":
            print("***crunch*** \n mmm. Thank you!")
            meal = randrange(self.food, self.food_max)
            self.food += meal
            if self.food > self.food_max:
                self.food = self.food_max
            self.clock_tick()
        else:
            print("Your pet died...")

    def play(self):
        if self.return_state() == "Alive":
            print("Woohoo!")
            fun = randrange(self.exicitement, self.exicitement_max)
            self.exicitement += fun
            if self.exicitement > self.exicitement_max:
                self.exicitement = self.exicitement_max
            self.clock_tick()
        else:
            print("Your pet died...") 
    
    def clean(self):
        if self.return_state() == "Alive":
            print("*Scrub*  *Scrub*  *Scrub*")
            scrub = randrange(self.hygene, self.hygene_max)
            self.hygene += scrub
            if self.hygene > self.hygene_max:
                self.hygene = self.hygene_max
            self.clock_tick()
        else:
            print("Your pet died...") 

        
    def get_state(self):
        return {
            'name': self.name,
            'animal_type': self.animal_type,
            'food': self.food,
            'exicitement': self.exicitement,
            'hygene' : self.hygene
        }
    
class PetApp:
    def __init__(self, master):
        self.master = master
        self.pet = load_game() if load_game() is not None else self.create_new_pet()
        
        master.title("Virtual Pet Game")

        self.status_button = tk.Button(master, text="Show Pet Status", command=self.show_pet_status)
        self.status_button.pack()

        self.feed_button = tk.Button(master, text="Feed Pet", command=self.feed_pet)
        self.feed_button.pack()

        self.teach_button = tk.Button(master, text="Teach your pet a new word", command=self.teach_pet)
        self.teach_button.pack()

        self.play_button = tk.Button(master, text="Play with Pet", command=self.play_pet)
        self.play_button.pack()

        self.clean_button = tk.Button(master, text="Clean Pet", command=self.clean_pet)
        self.clean_button.pack()

        self.save_button = tk.Button(master, text="Save Game", command=self.save_game)
        self.save_button.pack()

        self.delete_button = tk.Button(master, text="Delete Saved Game", command=self.delete_game)
        self.delete_button.pack()

        self.leave_button = tk.Button(master, text="Leave Game", command=self.leave_game)
        self.leave_button.pack()

    def leave_game(self):
        response = messagebox.askyesno("Leave Game", "Are you sure you want to leave the game?")
        if response:
            self.master.destroy()
            exit_program()

    def create_new_pet(self):
        name = simpledialog.askstring("Name", "What do you want to name your pet?", parent=self.master)
        animal_type = None
        while animal_type not in ["dog", "cat", "owl"]:
            animal_type = simpledialog.askstring("Type", "What is your pet? (Dog/Cat/Owl)", parent=self.master)
            if animal_type is None:
                messagebox.showinfo("Info", "Pet creation canceled.")
                return None
            if animal_type.lower() not in ["dog", "cat", "owl"]:
                messagebox.showwarning("Invalid Type", "Please enter a valid type: Dog, Cat, or Owl.")
        return Pet(name, animal_type.lower())

    def show_pet_status(self):
        status_window = Toplevel(self.master)
        status_window.title("Pet Status")
        status_text = self.get_pet_status()
        tk.Label(status_window, text=status_text).pack()
        tk.Button(status_window, text="OK", command=status_window.destroy).pack()
        self.pet.clock_tick()

    def get_pet_status(self):
        if self.pet.return_state() == "Alive":
            if self.pet.animal_type == "dog":
                random_word = random.choice(self.pet.vocab_dog)
            elif self.pet.animal_type == "cat":
                random_word = random.choice(self.pet.vocab_cat)
            else: 
                random_word = random.choice(self.pet.vocab_owl)
            return f"Name: {self.pet.name}, Type: {self.pet.animal_type}, Mood: {self.pet.mood()}, Says: {random_word}"
        else:
            return "Your pet died..."

    def teach_pet(self):
        new_word = simpledialog.askstring("Teach New Word", "What new word do you want to teach your pet?", parent=self.master)
        if new_word:  
            self.pet.teach(new_word)
            messagebox.showinfo("Success", f"You've taught your pet a new word: {new_word}!")
            
    def delete_game(self):
        delete_saved_game()
        messagebox.showinfo("Delete", "Saved game deleted successfully!")
        self.pet = self.create_new_pet()  

    def feed_pet(self):
        self.pet.feed()

    def play_pet(self):
        self.pet.play()

    def clean_pet(self):
        self.pet.clean()

    def save_game(self):
        save_game(self.pet)
        messagebox.showinfo("Save", "Game saved successfully!")

    def delete_game(self):
        delete_saved_game()
        messagebox.showinfo("Delete", "Saved game deleted successfully!")

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
        pet.hygene = data['hygene']
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
    root = tk.Tk()
    app = PetApp(root)
    root.mainloop()
    

def exit_program():
    print("Exiting the game...")
    sys.exit(0)

if __name__ == "__main__":
    
    main()