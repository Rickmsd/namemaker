## This is a simple game where the player is given several options for
## what a random couple should name their baby,
## or for what town a random character should move to,
## and they have to choose their favorite one.
## Maybe not the most entertaining game,
## but it's an example of how namemaker can be used in a project.

import random
import namemaker

N_OPTIONS = 4

def make_seed():
    ''' Makes a random string for use as an RNG seed.'''
    n = 30
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join(random.choice(alphabet) for _ in range(n))

def setup(seed):
    global male_names, female_names, unisex_names, uk_towns, pa_towns

    # Seed the random module so we can repeat this game if wanted.
    if seed is None:
        seed = make_seed()
    random.seed(seed)
    namemaker_rng = namemaker.get_rng()         # Since the namemaker module uses its own instance of random.Random,
    namemaker_rng.seed(seed)                    # we have to seed it, too, if we want the name generation to be repeatable.
    print(f'RNG seed: "{seed}"\n')

    # Make the name sets the game will use.
    # These are only created once so that they remember their history.
    male_names = namemaker.make_name_set('male first names')
    female_names = namemaker.make_name_set('female first names')
    unisex_names = male_names & female_names    # Names in the intersection of the male and female data.
    unisex_names.add('Pat')                     # Add a name that might not be in there yet, since it's more of a nickname.
    uk_towns = namemaker.make_name_set('England towns', name_len_func = namemaker.estimate_syllables)
    pa_towns = namemaker.make_name_set('PA towns', name_len_func = namemaker.estimate_syllables)

    # Link the histories of similar name sets.
    # This makes it so no names are repeated, even across name sets.
    male_names.link_histories(female_names, unisex_names)
    uk_towns.link_histories(pa_towns)

    # Reduce the order of the unisex name set so it can generate more names.
    # Since it has the least training data, it can't generate very many unique names.
    unisex_names.change_order(2)
    # >>> namemaker.stress_test(unisex_names, exclude_real_names = False, order = 3)
    # Unique generated names: 100
    # >>> namemaker.stress_test(unisex_names, exclude_real_names = False, order = 2)
    # Unique generated names: 4820
    # For all practical purposes, we don't have to worry about running out of names.

    # Block profanity from appearing in our generated names (though it's unlikely to begin with).
    banned_words = namemaker.get_names_from_file('horrendous profanity.txt')    # Get a list of banned words from a file.
    namemaker.set_banned_words(banned_words)                                    # Keep these words from appearing in any name from any name set.

def get_selection(options):
    ''' Print all the input options and let the player pick one.
        Returns the selected option.'''
    for i, name in enumerate(options):
        print(f'{i+1}: {name}')

    while True:
        player_input = input('Enter the number of your selection: ')
        try:
            selection_index = int(player_input) - 1
        except ValueError:
            pass
        else:
            if 0 <= selection_index < len(options):
                return options[selection_index]
        print('Please enter a number shown before one of the options.')

def baby_name():
    ''' Make several random baby names and let the player choose one.'''
    gender_names = {'son': male_names,
                    'daughter': female_names,
                    'child': unisex_names}
    mother = female_names.make_name()       # Use the male and female name sets to make names for the parents.
    father = male_names.make_name()
    child = random.choice(list(gender_names))
    child_name_set = gender_names[child]    # Choose the correct name set for the gender of the child.
    print(f'What should {father} and {mother} name their {child}?')

    options = []
    for _ in range(N_OPTIONS):
        name = child_name_set.make_name(exclude_real_names = False)
        options.append(name)
    selected_name = get_selection(options)
    print(f'{father} and {mother} name their {child} {selected_name}.\n')

def town_name():
    ''' Make several random town names and let the player choose one.'''
    person_name_set = random.choice([male_names, female_names])
    person = person_name_set.make_name()
    print(f'Where should {person} move?')

    town_name_set = random.choice([uk_towns, pa_towns])
    options = []
    for _ in range(N_OPTIONS):
        name = town_name_set.make_name(validation_func = namemaker.validate_town)   # Use namemaker's built in town validation function to avoid strange town names.
        options.append(name)
    selected_town = get_selection(options)
    print(f'{person} moves to {selected_town}.\n')

def main(seed = None):
    print('Press ctrl+c to quit.\n')
    setup(seed)
    question_funcs = [baby_name, town_name]
    try:
        while True:
            question_func = random.choice(question_funcs)
            question_func()
    except KeyboardInterrupt:
        print('\nThank you for playing!\n')

if __name__ == '__main__':
    main()






