# What is namemaker?
Namemaker is a random name generator.  Use it to procedurally create names for places and characters in a game, or to break through writer's block while trying to come up with handcrafted names.  Input your own training data to make any kind of names you want.

# Useful features
* Several built-in training data sets to get different "sounds" to your names.
* Ability to use your own training data.
* Control over the realism and length of generated names.
* Full control of the RNG to make name generation repeatable.
* Ability to ban profanity or other words from appearing in generated names.
* Ability to place arbitrary restrictions on the generated names.
* Avoidance of repeated names by default.

# How to install
Use pip in your command line.

```
pip install namemaker
```

# Quick start
Namemaker uses a class called a NameSet to store training data and make fake names from it.  Training data can be loaded from a text file.

```python
>>> import namemaker
>>> female_names = namemaker.make_name_set('female first names.txt')
>>> female_names.make_name()
'Lyricia'
```

You can also use the `sample` function to quickly get an idea of what kind of names your inputs will produce.  Any keyword arguments accepted by `make_name_set` or `NameSet.make_name` are accepted by `sample`.  It also takes an argument `n` that determines how many sample names to print.

```python
>>> namemaker.sample(female_names, n = 10)
Nayah
Samandry
Graci
Kenne
Malanna
Julina
Carlie
Alondon
Elene
Clarai
```

# How does it work?
The name generator uses Markov chains to make fake names based on a training set of real names.  When a NameSet is initialized, it looks through all the training data and maps out which letters can follow each combination of other letters.  The `order` parameter determines the order of the Markov chain, i.e. how many letters are used for matching.  For example, when you call `make_name_set(['John', 'Joey', 'Joseph'], order = 2)`, the NameSet knows that the letter combination `'Jo'` can be followed by `'h'`, `'e'`, or `'s'`.  If you're curious, you can see all the letter combinations by looking at the NameSet's `_markov_dict`.

```python
>>> j_names = namemaker.make_name_set(['John', 'Joey', 'Joseph'], order = 2)
>>> j_names._markov_dict
{'': ['J', 'J', 'J'], 'J': ['o', 'o', 'o'], 'Jo': ['h', 'e', 's'], 'oh': ['n'], 'hn': [None], 'oe': ['y'], 'ey': [None], 'os': ['e'], 'se': ['p'], 'ep': ['h'], 'ph': [None]}
```

Note that the `_markov_dict` shouldn't be accessed directly in your program, though, as the leading underscore denotes it as a private attribute.

# Making NameSets
The preferred way to make a NameSet is with the `make_name_set` function:

```python
make_name_set(names, order = 3, name_len_func = len, clean_up = True)
```

The input `names` is the training data for the NameSet.  It can be a container of names (such as a list, set, tuple, or another NameSet), or a string specifying a file where names are stored.  Namemaker comes with some starter files of training data, listed below:

* `male first names.txt` [1]
* `female first names.txt` [2]
* `last names.txt` [3]
* `England towns.txt` [4]
* `PA towns.txt` [5]
* `Greek mythology.txt` [6]

Modifying the `order` parameter affects how realistic the generated names sound.  At `order = 1`, they are mostly gibberish, and sometimes unpronounceable.

```python
>>> namemaker.sample('male first names.txt', n = 10, order = 1)
Rhacam
Min
Mana
Brich
Alamid
Janen
Restthan
Cannd
Caxt
Chulks
```

At `order = 2` or `order = 3` (the default), they still tend to sound fantastical or futuristic, but they should now avoid any unusual letter combinations.

```python
>>> sample('male first names', n = 10, order = 2)
Grius
Dwarc
Fis
Nik
Alannox
Mosel
Juar
Lukaid
Ahmano
Carick
```

```python
>>> sample('male first names', n = 10, order = 3)
Dylark
Kayder
Domington
Ronny
Donard
Remiah
Eugendry
Silan
Leonan
Baylon
```

At `order = 4`, they tend to sound like realistic but somewhat unusual names.

```python
>>> sample('male first names', n = 10, order = 4)
Jamien
Dyland
Hendrick
Philles
Lando
Killie
Deckett
Marlos
Willip
Elises
```

The default is `order = 3` because it strikes a good balance between randomness and realism for a variety of training data.  It avoids unnatural letter combinations while not appearing as a misspelling of a common real name.  Of course, this “sweet spot” may vary depending on your training data and what you want your names to look like.

The `name_len_func` is a function that measures some property of a name (length, by default).  See the “Making names” section for details on how the `name_len_func` is used.

The final argument in `make_name_set` is `clean_up`.  This determines if the training data will be cleaned up using `namemaker.clean`, described in the “Finding and processing training data” section.

Since making a NameSet involves lots of pre-calculation and (possibly) reading data from the disk, it's recommended that you only do it once as a setup step.

# Making names
Now that you've used `make_name_set` to make a NameSet out of your training data, it's time to make some random names.  The `NameSet.make_name` method has a lot of inputs, but most of them are set to “just work” by default.  The possible inputs to `make_name` and their default values are shown below:

```python
exclude_real_names = True
exclude_history = True
add_to_history = True
n_candidates = 2
pref_candidate = AVG
max_attempts = 1000
validation_func = None
```

Starting simple, `exclude_real_names` will keep `make_name` from outputting any name that's already in your training data.  For instance, a NameSet made with the included `male first names.txt` file won't make the name “John” if `exclude_real_names = True`.

The next two inputs, `exclude_history` and `add_to_history`, are closely related.  By default, each NameSet keeps track of the names it's already made to avoid repeats.  When using `add_to_history = True`, the NameSet will remember the name returned by`make_name`.  If `exclude_history` is True, `make_name` won't make any name that's already remembered in the NameSet's history.

Internally, `make_name` actually generates a few names and picks what it thinks is the best one.  By default, it chooses the name closest to the average length of the training data, as measured by the NameSet's `name_len_func`.  The number of name candidates it chooses from is specified by `n_candidates`.  The default is 2 because it allows a variety of name lengths to get through, while still weeding out the extremely long or short outliers.  Increasing `n_candidates` reduces the variance in name length (or whatever property is checked by `name_len_func`).

`pref_candidate` is the method used to select the best name candidate.  Possible values are `namemaker.MIN`, `namemaker.MAX`, and `namemaker.AVG` (0, 1, and 2, respectively).  The default is `AVG`, which picks the name candidate that best matches the average length of the training data (as determined by `name_len_func`).  `MIN` and `MAX` will choose the shortest and longest name, respectively, as determined by `name_len_func`.

Under extreme circumstances, it is possible for `make_name` to fail to make a valid name, in which case it returns an empty string.  `max_attempts` is the number of times it tries (per name candidate) before giving up.  See below for some reasons that `make_name` might fail.

There may be a number of limits you want to impose on the names created by `make_name`, and the `validation_func` provides an easy way to do it.  If present, it must be a function that takes in a single name as a string, and returns `True` if that name is acceptable and `False` if not.  A few possible uses:

* Provide a minimum or maximum allowable length.  Ex:  `validation_func = lambda name: len(name) <= 16`
* Exclude a common misspelling.  Ex:  `validation_func = lambda name: not name.endswith('vill')` excludes any town names ending in “vill” instead of “ville”.
* Exclude two-word names:  `validation_func = lambda name: ' ' not in name`

## Banning words
You can ban certain words from appearing in your names.  The namemaker module has a global set of banned words, which is empty by default.  You can set the banned words or add words to the banned word set with the `set_banned_words` or `add_banned_words` functions.  `get_banned_words` lets you check your banned words.  Banned words are not case sensitive, and `NameSet.make_name` will not return a name that contains a banned word.

## Reasons make_name might fail

* There are too few names in the training data, and `exclude_real_names = True`.  If there isn't enough variety in the possible letter combinations, a Markov chain may only be able to make names that are already in the training data.
* Your `validation_func` is too restrictive.
* Your set of banned words is too restrictive.
* There are a lot of names in the NameSet's history, and `exclude_history = True`.  This is not very likely, as a NameSet with a reasonable amount of training data can generate over 10 unique names per training name.  Example: At 277 names, `Greek mythology.txt` is the shortest built-in training data file, and it can generate about 3800 names (with default settings) before failing from a full history.

# Finding and processing training data
The main advantage of namemaker is its ability to emulate the “sound” of its training data, and, by extension, its customizability by providing your own training data.  The internet is full of lists of things.  A helpful trick is to copy an entire list or table of names into a spreadsheet program like Excel, delete unwanted columns and rows, then save as a tab-delimited text file.  Namemaker expects text files to contain one name per row.

When importing this data into namemaker, there are several options for cleaning it of unwanted junk.  The default behavior used by `make_name_set` is to first strip off any non-alphanumeric symbols from the beginning and end of each name, then remove any empty names.  There may be cases when you want to avoid this behavior.  For instance, in a training set of band names, “Wham!” would be reduced to “Wham”, robbing you of the opportunity to generate names that end in an exclamation point.  In a case like this, you can call `make_name_set` with `clean = False`.  You can also do the clean-up step manually for greater control, as shown below:

```python
my_names = get_names_from_file('my name file')
my_names = clean_blanks(my_names, blank_names = ['N/A', 'null'])
my_name_set = make_name_set(my_names, clean_up = False)
```

In this example, you're not removing any symbols from the ends of your names, but are still removing any empty names and names that were saved in your file as 'N/A' or 'null'.  The ability to specify names that count as “blank” allows you to copy from messy or incomplete data sources without having to do too much manual cleanup.

## Functions for importing and cleaning data:

* `get_names_from_file(file_name)`:  Loads names from a file and returns them in a list.
* `clean(names)`:  First strips non-alphanumeric characters from the beginning and end of the names, then removes any blank names from the list.  Returns a new list.
* `clean_blanks(names, blank_names = [])`:  Gets rid of any names that consist solely of non-alphanumeric characters, as well as any names specified in `blank_names`.  Returns a new list.
* `clean_extra_symbols(names)`:  Strips non-alphanumeric characters from the beginning and end of the names.  Returns a new list.
* `strip_non_alnum(name)`:  Strips non-alphanumeric characters from the beginning and end of a single name.  Returns a string.

# Manipulating NameSets
While a typical usage of namemaker involves loading up some training data into a NameSet and using it as-is, NameSets can also be combined and altered in a variety of ways.

Addition with the `+` and `+=` operators:  This combines two NameSets, or a NameSet and any other collection of names, while preserving duplicate names.  That is, any name in both NameSets will end up in the resulting NameSet twice.  Compare to list addition.  Duplicate names will be twice as likely to have their letter combinations show up in the results of `make_name`.

Subtraction with the `-` and `-=` operators:  This removes any names in one NameSet (or other collection of names) from another NameSet.  If the original NameSet had duplicate names in it, only the amount present in the subtracted NameSet will be removed.  Pseudocode example:  `NameSet(['Jack', 'John', 'John']) - NameSet(['John', 'Jacob']) = NameSet(['Jack', 'John'])`.

Union with the `|` and `|=` operators:  This combines two NameSets, or a NameSet and any other collection of names, but only counts duplicate names once.  Compare to set union.  The result will have no duplicate names.

Intersection with the `&` and `&=` operators:  This keeps only the overlapping parts of two NameSets, or a NameSet and any other collection of names.  It's not a direct analog to set intersection because it allows for duplicate names as long as they are present in both original NameSets.  Pseudocode example:  `NameSet(['Jack', 'John', 'John']) & NameSet(['John', 'John', 'John']) = NameSet(['John', 'John'])`.

Any of the above operators can be used with a NameSet and any collection of names, like a list, set, tuple, or other NameSet.  For the in-place operators, the NameSet must come first.  In the case of two NameSets of different `order` or different `name_len_func`, the attributes of the NameSet on the left side of the operator are preserved in the result, and a warning is raised.  For the in-place operators, the modified NameSet will retain its original history.  For the normal operators, the resultant NameSet will have no history.

NameSets have some other methods to modify themselves, too:

`append(name)`:  Appends a single name to the NameSet, regardless of if the name is already in the NameSet.  Compare list.append.

`add(name)`:  Adds a single name to the NameSet if it's not in it already.  Compare set.add.

`remove(name)`:  Removes a single name from the NameSet if it's in it, or raises a ValueError if not.  Only removes the name once if it's duplicated in the NameSet.  Compare list.remove.

`remove_duplicates()`:  Reduces the NameSet so that each of its names is present exactly once.

`copy()`:  Returns a deep copy of the NameSet.

`change_order(order)`:  Changes the order of the Markov chains used to make names.

`change_name_len_func(name_len_func)`:  Changes the function used to calculate name length.

`clear_history()`:  Deletes the history of names made by `make_name`.

`add_to_history(name_s)`:  Adds the input name or collection of names to the NameSet’s history.

`link_histories(*other_name_sets)`:  (New in version 1.1) Links the history of the NameSet to the histories of all the other_name_sets.  Adding a name to the history of one will add it to all the linked histories.  This is useful if you have several NameSets that might generate similar names, but don't want any repeated names within the group.  This method breaks any existing linked histories in the NameSet and the other_name_sets.

`unlink_history()`:  (New in version 1.1) Breaks any linked histories that the NameSet might have, without breaking the links among other NameSets in the linked group.

Example of history linking:

```python
male_names = namemaker.make_name_set('male first names', order = 2)
female_names = namemaker.make_name_set('female first names', order = 2)
male_names.link_histories(female_names)
```

In this case, you might want to generate male or female names, without repeating a previous male name as a female name or vice versa.

# Warnings
Namemaker uses a few custom warnings to avoid interfering with any warning filters you've set up in your own code.

`OrderWarning`:  This is raised when an operation is performed on two NameSets of different order.  A warning filter ensures that it gets shown every time such an operation is performed.  Example:

```python
>>> a = namemaker.make_name_set(['John', 'Jack', 'Jake'], order = 2)
>>> b = namemaker.make_name_set(['Fred', 'Frank', 'Francis'], order = 3)
>>> c = a + b

Warning (from warnings module):
  File "<pyshell#6>", line 1
OrderWarning: Adding NameSet of order 3 to NameSet of order 2. Result will be of order 2.
```

`NameLenWarning`:  This is raised when an operation is performed on two NameSets using different `name_len_func`s.  A warning filter ensures that it gets shown every time such an operation is performed.

`CopyWarning`:  This is raised when calling `copy.copy` on a NameSet, because NameSets do not support shallow copying.

# Managing the Random Number Generator
Namemaker uses Python's built-in `random` module, but uses its own instance of `random.Random` to avoid interfering with the state of the `random` module.  You can access the RNG with the `namemaker.get_rng` function.  Being an instance of `random.Random`, it supports all the same methods as the `random` module itself, like `getstate`, `setstate`, and `seed`.  You can also replace the default RNG with your own RNG, using `namemaker.set_rng(my_rng)`.  The only requirement on `my_rng` is that it has a `choice` method that takes in a list and returns a single element from that list.

# Misc. functions
`estimate_syllables(name)`:  Returns an estimate of how many syllables are in a string.  It's only an estimate, but gets pretty close for most strings.  It can be used as a `name_len_func`.

`stress_test(names, **kwargs)`:  Similar to sample, but instead of printing names, it runs NameSet.make_name until it fails to make a name, then prints info about how many names were made compared to the number of names in the training data.  It probably isn't of much practical use, as most NameSets will generate thousands of names before failing.  Its main purpose is to show that most training data can generate more than enough names for practical purposes, even when avoiding repeats.

# Cookbook
Here are some different uses of namemaker to provide an idea of how the inputs can be varied for different results.

Planet names using the built-in Greek mythology data:

```python
>>> sample('Greek mythology', n = 10, order = 2)
Hypnonus
Daritracus
Elegon
Ancalias
Amphous
Priama
Hestes
Iacis
Iphimerope
Endis
```

Short and punchy town names:

```python
>>> namemaker.sample('PA towns', n = 10,
         n_candidates = 20,
         pref_candidate = namemaker.MIN,
         name_len_func = namemaker.estimate_syllables)
Hall
Slights
Cree
Treek
Smeth
Broads
Fair
Chest
Glen
Greath
```

Absurd town names.  The `validation_func` is preventing odd combinations of prepositions.  You may find it necessary to add others if you use this recipe for real:

```python
>>> preposition_combos = ['on-upon', 'upon-on', 'on-by', 'by-on', 'in-on', 'on-in']
>>> namemaker.sample('England towns', n = 10,
       n_candidates = 20,  # Make lots of candidates and choose the longest one
       pref_candidate = namemaker.MAX,
       validation_func = lambda name: not any(x in name for x in preposition_combos)
                                      and not name.endswith(' and'))
Eastleby-in-Furntworthwellingham
Whitnes-upon-Cleobury
Royal Leamingdenham
Snaith-Wolsingden Aycliffield
Ching Carlborouch witherley
Ingleby-in-Furnham Streesallington upon-Humbergh-in-Arden
Bark-on-West Gringham
Leominsteland Castleby Welwyn Garst
New Minsterton Spa
Madebroughbridge
```

Fantastical or evil-sounding item names (e.g. “The Sword of ...”):

```python
>>> namemaker.sample('PA towns', n = 10,
         order = 1,
         name_len_func = lambda name: sum(letter not in 'AEIOUaeiou' for letter in 'name'), # don't count vowels toward name length
         pref_candidate = namemaker.MAX,                                       # maximize consonants
         validation_func = lambda name: 4 < len(name) <= 8
                                        and any(n in 'aeiou' for n in name)) # make sure there's a vowel in there somewhere
Fildron
Sootostz
Cilllch
Coielty
Sudtenhf
Bellen
S. Hing
Jalllan
Stilal
Les Mee
```

# Sources of built-in training data
[1] BABY NAMES IN AMERICA: Most Popular Baby Names for Boys in America, *NameCensus.com*, accessed at https://namecensus.com/baby_names/boys250.html

[2] BABY NAMES IN AMERICA: Most Popular Baby Names for Girls in America, *NameCensus.com*, accessed at https://namecensus.com/baby_names/girls250.html

[3] What is the most common last name in the United States?, *NameCensus.com*, accessed at https://namecensus.com/data/1000.html

[4] List of towns in England, *Wikipedia*, accessed at https://en.wikipedia.org/wiki/List_of_towns_in_England

[5] List of towns and boroughs in Pennsylvania, *Wikipedia*, accessed at https://en.wikipedia.org/wiki/List_of_towns_and_boroughs_in_Pennsylvania

[6] List of Greek mythological figures, *Encyclopedia Britannica*, accessed at https://www.britannica.com/topic/list-of-Greek-mythological-figures-2027488