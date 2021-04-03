''' Module for using Markov chains to generate random names.'''
import random
import warnings
import pkgutil

## NOTE: name data should be saved as txt files with each entry on its own line

DEFAULT_MAX_ATTEMPTS = 1000
DEFAULT_N_CANDIDATES = 2
DEFAULT_ORDER = 3
DEFAULT_NAME_LEN_FUNC = len
MIN, MAX, AVG = range(3)
_BUILTIN_NAMES_FOLDER = 'name data'
_PASS_EVERYTHING = lambda name: True
_END = None     # denotes the end of a name in a Markov chain

banned_words = set()

'======================================================= Warning handling ====================================================='

# Define two wrappers of UserWarning to use in cases when two NameSets have mismatched order or name_len_func.
# Then a filter is set to always show these warnings,
# without interfering with the default filter or any user-defined filters for UserWarning.

class OrderWarning(UserWarning):
    pass

class NameLenWarning(UserWarning):
    pass

class CopyWarning(UserWarning):
    ''' Used if the user tries to call copy.copy on a NameSet,
        since the NameSet's behavior of returning a deep copy in this case
        is contrary to how copy.copy usually works.'''
    pass

warnings.simplefilter('always', OrderWarning)
warnings.simplefilter('always', NameLenWarning)

'======================================================= RNG handling ========================================================='

rng = random.Random()

def get_rng():
    ''' Returns this module's global random number generator,
        by default an instance of random.Random'''
    return rng

def set_rng(new_rng):
    ''' Sets a new global random number generator for this module.
        new_rng must have a 'choice' method that takes in a list
        and returns one item from that list.'''
    global rng
    rng = new_rng

'======================================================= NameSet definition ==================================================='

class NameSet():
    ''' A class to store name data and make names.'''

    def __init__(self, names = [], order = DEFAULT_ORDER, name_len_func = DEFAULT_NAME_LEN_FUNC):
        if int(order) != order:         # insanity check
            raise ValueError('Can\'t create NameSet with non-integer order.')
        if order < 0:
            raise ValueError('Can\'t create NameSet with negative order.')
        self._names = list(names)       # Make a copy of the input name collection so the original won't ever mutate
        self._names_set = set(names)    # This exists solely to improve performance when calling make_name with exclude_real_names = True
        self._order = order
        self._name_len_func = name_len_func
        self._update_avg_name_len()     # sets the attribute self._avg_name_len
        self._make_markov_dict()        # sets the attribute self._markov_dict
        self._history = set()
        self._in_operation = False      # for use when raising a warning, to avoid calling the warning from an operation like '+'

    def __str__(self):
        return f'{self._names}, order = {self._order}'

    def copy(self):
        ''' Creates and returns a new NameSet object identical to this one.
            This is a deep copy.
            If this NameSet has its history linked to any other NameSets,
            the copy's history will not be linked.'''
        copy_set = NameSet(order = self._order, name_len_func = self.get_name_len_func())
        copy_set._names = self._names[:]
        copy_set._names_set = {*self._names_set}
        copy_set._markov_dict = {key: letters[:] for key, letters in self._markov_dict.items()}     # Have to copy the lists within this dict, not just copy the dict itself.
                                                                                                    # Otherwise, two apparently seperate NameSets will have their morkov_dicts coupled.
        copy_set._avg_name_len = self._avg_name_len
        copy_set._history = {*self._history}
        return copy_set

    def __deepcopy__(self, memo):
        return self.copy()

    def __copy__(self):
        warnings.warn('NameSet does not support shallow copying. Returning a deep copy.', category = CopyWarning, stacklevel = 3)
        return self.copy()

    def __eq__(self, other_set):
        ''' Two NameSets are equal if all of their attributes are equal.
            A NameSet can't be equal to anything but another NameSet.'''
        # Comparing all attributes, even ones that are dependent on others (like _avg_name_len and _names_set)
        # ensures that the equality result is accurate even if the user tampers with private attributes.
        return type(other_set) is NameSet and self.__dict__ == other_set.__dict__

    def __iter__(self):
        ''' Iterate over this NameSet's training data.'''
        return _NameSetIterator(self)

    def __len__(self):
        ''' Length of this NameSet's training data.'''
        return len(self._names)

    def __getitem__(self, index):
        ''' Gets the name at input index from this NameSet's training data.'''
        return self._names[index]

    def __contains__(self, item):
        ''' True if the input item is in this NameSet's training data.'''
        return item in self._names_set

    def __add__(self, other_name_set):
        ''' Adds two NameSets using + operator and returns a new NameSet object.
            other_name_set can be a NameSet or any container of names.
            Duplicate names are counted twice.
            The returned NameSet has no history.'''
        copy_set = self.copy()
        copy_set._in_operation = True
        copy_set += other_name_set
        copy_set.clear_history()
        copy_set._in_operation = False
        return copy_set

    def __iadd__(self, other_name_set):
        ''' Modifies this data set and adds the new names to it,
            using the += operator.
            Duplicate names are added again.
            If duplicate names are not desired, use the |= operator.
            other_name_set can be a NameSet or any container of names.
            Keeps the order of this NameSet, even if other_name_set has a
            different order.
            Does not modify this NameSet's history.'''

        if type(other_name_set) is str:
            raise TypeError('Cannot add str to NameSet. Use NameSet.append instead.')

        if type(other_name_set) is not NameSet:
            other_name_set = NameSet(names = other_name_set, order = self.get_order(), name_len_func = self.get_name_len_func())

        if self._order != other_name_set._order:
            warnings.warn(f'Adding NameSet of order {other_name_set.get_order()} to NameSet of order {self.get_order()}. '
                          f'Result will be of order {self.get_order()}.', category = OrderWarning, stacklevel = 2 + int(self._in_operation))
            other_name_set = other_name_set.copy()
            other_name_set.change_order(self._order)

        if self.get_name_len_func() is not other_name_set.get_name_len_func():
            warnings.warn(f'Adding NameSet with name_len_func {other_name_set.get_name_len_func()} '
                          f'to NameSet with name_len_func {self.get_name_len_func()}. Result will use {self.get_name_len_func()}.',
                          category = NameLenWarning, stacklevel = 2 + int(self._in_operation))
            other_name_set = other_name_set.copy()
            other_name_set.change_name_len_func(self.get_name_len_func())

        self._avg_name_len = (self._avg_name_len * len(self) + other_name_set._avg_name_len * len(other_name_set)) / (len(self) + len(other_name_set))

        self._names += other_name_set._names
        self._names_set |= other_name_set._names_set
        for k, v in other_name_set._markov_dict.items():    # add the values of the other set's markov_dict
            if k in self._markov_dict:
                self._markov_dict[k] += v
            else:
                self._markov_dict[k] = v

        return self

    def __sub__(self, other_names):
        ''' Subtracts other_names from the NameSet using the - operator.
            other_names can be a NameSet or any container of names.
            Returns a new NameSet object, and does not modify this one.
            The returned NameSet has no history.'''
        copy_set = self.copy()
        copy_set._in_operation = True
        copy_set -= other_names
        copy_set.clear_history()
        copy_set._in_operation = False
        return copy_set

    def __isub__(self, other_names):
        ''' Subtracts other_names from the NameSet using the -= operator.
            Modifies this NameSet in place.
            Does not modify this NameSet's history.'''

        if type(other_names) is str:
            raise TypeError('Cannot subtract str from NameSet. Use NameSet.remove instead.')

        if type(other_names) is NameSet:
            if self._order != other_names._order:
                warnings.warn(f'Subtracting NameSet of order {other_names.get_order()} from NameSet of order {self.get_order()}. '
                              f'Result will be of order {self.get_order()}.', category = OrderWarning, stacklevel = 2 + int(self._in_operation))

            if self.get_name_len_func() is not other_names.get_name_len_func():
                warnings.warn(f'Subtracting NameSet with name_len_func {other_names.get_name_len_func()} '
                              f'from NameSet with name_len_func {self.get_name_len_func()}. Result will use {self.get_name_len_func()}.',
                              category = NameLenWarning, stacklevel = 2 + int(self._in_operation))

        # Don't remove. Keep for reference.
##        other_names = set(other_names)
##        self._names = [name for name in self._names if name not in other_names]
##        self._names_set -= other_names
##        self._make_markov_dict()
##        self._update_avg_name_len()
##        return self

        # Removing every name of other_names from this NameSet might not be very performant because of repeated calles to list.remove,
        # but it allows subtraction to remove only the number of repeated names that were in other_names.
        # I.e. if this NameSet has the name 'John' in it three times, and the subtracted other_names has 'John' in it two times,
        # there will still be one instance of 'John' in this NameSet after subtraction.
        # If the commented-out method above was used, there would be no instances of 'John' left after subtraction.

        for name in other_names:        
            if name in self:
                self.remove(name)
        return self

    def __or__(self, other_name_set):
        ''' Union of this NameSet with another collection of names
            using the | operator.
            other_name_set can be a NameSet or any container of names.
            Does not modify this set, and returns a new NameSet object.
            Names are only counted once. All duplicates are removed.
            The returned NameSet has no history.'''
        copy_set = self.copy()
        copy_set._in_operation = True
        copy_set |= other_name_set
        copy_set.clear_history()
        copy_set._in_operation = False
        return copy_set

    def __ior__(self, other_name_set):
        ''' Takes the union of this NameSet with another collection of names,
            using the |= operator.
            Modifies this NameSet in place.
            Each name is only counted once.
            ALL duplicates are removed from this NameSet.
            other_name_set can be a NameSet or any container of names.
            Keeps the order of this NameSet,
            even if other_name_set has a different order.
            Does not modify this NameSet's history.'''

        if type(other_name_set) is str:
            raise TypeError('Cannot take union of str and NameSet. Use NameSet.add instead.')
        
        if type(other_name_set) is NameSet:
            if self._order != other_name_set._order:
                warnings.warn(f'Taking union of NameSet of order {other_name_set.get_order()} into NameSet of order {self.get_order()}. '
                              f'Result will be of order {self.get_order()}.', category = OrderWarning, stacklevel = 2 + int(self._in_operation))

            if self.get_name_len_func() is not other_name_set.get_name_len_func():
                warnings.warn(f'Taking union of NameSet with name_len_func {other_name_set.get_name_len_func()} '
                              f'into NameSet with name_len_func {self.get_name_len_func()}. Result will use {self.get_name_len_func()}.',
                              category = NameLenWarning, stacklevel = 2 + int(self._in_operation))

        new_names = [name for name in other_name_set if name not in self]   # this step would be taken care of by self.remove_duplicates() anyway,
                                                                            # but it's probably better for performance to minimize calls to self.remove
                                                                            # because removing an item from a list is costly
        self += new_names
        self.remove_duplicates()
        return self

    def __and__(self, other_name_set):
        ''' Intersection of this NameSet with another collection of names
            using the & operator.
            other_name_set can be a NameSet or any container of names.
            Does not modify this set, and returns a new NameSet object.
            The returned NameSet has no history.'''
        copy_set = self.copy()
        copy_set._in_operation = True
        copy_set &= other_name_set
        copy_set.clear_history()
        copy_set._in_operation = False
        return copy_set

    def __iand__(self, other_name_set):
        ''' Intersection of this NameSet with another collection of names
            using the &= operator.
            other_name_set can be a NameSet or any container of names.
            Modifies this NameSet in place.
            Does not modify this NameSet's history.'''

        if type(other_name_set) is str:
            raise TypeError('Cannot take intersection of str with NameSet.')

        if type(other_name_set) is NameSet:
            if self._order != other_name_set._order:
                warnings.warn(f'Taking intersection of NameSet of order {other_name_set.get_order()} into NameSet of order {self.get_order()}. '
                              f'Result will be of order {self.get_order()}.', category = OrderWarning, stacklevel = 2 + int(self._in_operation))

            if self.get_name_len_func() is not other_name_set.get_name_len_func():
                warnings.warn(f'Taking intersection of NameSet with name_len_func {other_name_set.get_name_len_func()} '
                              f'into NameSet with name_len_func {self.get_name_len_func()}. Result will use {self.get_name_len_func()}.',
                              category = NameLenWarning, stacklevel = 2 + int(self._in_operation))

        # Don't remove. Keep for reference.
##        unshared_names = [name for name in self._names if name not in other_name_set]
##        self -= unshared_names
##        return self

        # This method ensures that only the correct number of duplicate shared names are in the result,
        # i.e. if this NameSet has 'John' in it three times and other_name_set has 'John' in it twice,
        # the result will have 'John' in it two times.
        # The previous method would always have this NameSet's number of duplicate names
        # even if the other_name_set had fewer.
        other_names_list = list(other_name_set)
        shared_names = []
        for name in self:
            if name in other_names_list:
                shared_names.append(name)
                other_names_list.remove(name)
        self._names = shared_names
        self._names_set = set(shared_names)
        self._make_markov_dict()
        self._update_avg_name_len()
        return self

    def add(self, name):
        ''' Adds the name to the NameSet if it is not already in it.
            Compare set.add'''
        if name not in self:
            self.append(name)

    def append(self, name):
        ''' Appends the name to the NameSet whether it is already in it or not.
            Compare list.append'''
        self += [name]

    def remove(self, name):
        ''' Removes the name from the NameSet.
            Raises a ValueError if the name is not in the NameSet.'''
        try:
            self._names.remove(name)
            if name not in self._names:
                self._names_set.remove(name)
        except ValueError as error:         # don't handle KeyError because the name must be in the _names_set if it was in the _names list.
            raise ValueError('Input name is not in the NameSet.') from error

        # Get rid of the name's letters from the markov_dict
        remove_name_set = NameSet([name], order = self.get_order())
        for key, remove_letters in remove_name_set._markov_dict.items():
            for letter in remove_letters:
                self._markov_dict[key].remove(letter)
            if not self._markov_dict[key]:  # delete the whole key from the markov dict if it only had letters from the removed name
                del(self._markov_dict[key])

        # Update the average name len without calling _update_avg_name_len, because that involves calling name_len_func for every name in the NameSet
        sum_lengths = self._avg_name_len * (len(self) + 1)  # the +1 is because the NameSet is now 1 name shorter than it was when _avg_name_len was calculated
        sum_lengths -= len(name)
        self._avg_name_len = sum_lengths / len(self)

    def remove_duplicates(self):
        ''' Removes any duplicated names from the NameSet so there is only one
            of each name.'''
        names_set = set()
        for name in self._names[:]:
            if name in names_set:
                self.remove(name)
            else:
                names_set.add(name)

    def change_order(self, order):
        ''' Changes the order of the NameSet and recalculates the markov_dict.'''
        if int(order) != order:         # insanity check
            raise ValueError('Can\'t change to a non-integer order.')
        if order < 0:
            raise ValueError('Can\'t change to a negative order.')
        self._order = order
        self._make_markov_dict()

    def change_name_len_func(self, name_len_func):
        ''' Changes the NameSet's name_len_func
            and recalculates the avg_name_len based on the new name_len_func.'''
        self._name_len_func = name_len_func
        self._update_avg_name_len()

    def get_order(self):
        ''' Returns the Markov chain order of this NameSet,
            i.e. how many letters are used for matching.'''
        return self._order

    def get_name_len_func(self):
        ''' Returns the function used to calculate the length of names
            in this NameSet.'''
        return self._name_len_func

    def get_avg_name_len(self):
        ''' Returns the average length of the names in this NameSet,
            as calculated by its name_len_func.'''
        return self._avg_name_len

    def get_history(self):
        ''' Returns a copy of this NameSet's history.'''
        return {*self._history}

    def add_to_history(self, name_s):
        ''' Adds the input name or names to this NameSet's history.
            name_s can be a single name input as a string,
            or a collection of names in the form of a NameSet,
            list, set, or other iterable.'''
        if type(name_s) is str:
            name_s = {name_s}
        self._history |= set(name_s)

    def clear_history(self):
        ''' Clears the name history of this NameSet.
            If any other NameSets have their history linked,
            it clears them, too.'''
        self._history.clear()

    def link_histories(self, *other_name_sets):
        ''' Links the hisories of this NameSet and all input other_name_sets
            so that adding a name to the history of one adds it to all.
            Is useful for groups of NameSets that might generate similar names.
            The existing histories of all linked NameSets are combined.
            This breaks any linked histories that this NameSet or any of the
            other_name_sets already have.'''
        other_histories = [s._history for s in other_name_sets]
        shared_history = self._history.union(*other_histories)
        self._history = shared_history
        for s in other_name_sets:
            s._history = shared_history

    def unlink_history(self):
        ''' Breaks any linked histories that this NameSet might have.
            It retains its current history.'''
        self._history = {*self._history}

    def _update_avg_name_len(self):
        if self._names:
            self._avg_name_len = sum([self._name_len_func(name) for name in self._names]) / len(self._names)
        else:
            self._avg_name_len = 0

    def _make_markov_dict(self):
        self._markov_dict = {}
        for name in self._names:
            previous_letter = ''
            for letter in name:
                try:
                    self._markov_dict[previous_letter].append( letter )
                except KeyError:
                    self._markov_dict[previous_letter] = [letter]
                previous_letter += letter
                if len(previous_letter) > self._order:
                    previous_letter = previous_letter[1:]

            # Use None to denote the end of the name
            try:
                self._markov_dict[previous_letter].append(_END)
            except KeyError:
                self._markov_dict[previous_letter] = [_END]

    def _get_letter(self, key):
        try:
            return rng.choice(self._markov_dict[key])
        except (KeyError, IndexError):
            return _END     # End the name if the key is somehow not in the markov_dict or if there are no options for that key.
                            # Neither of these should ever happen

    def _make_name_raw(self):
        name = ''
        next_letter_key = ''
        while True:
            next_letter = self._get_letter(next_letter_key)
            if next_letter is _END:
                break
            name += next_letter
            next_letter_key += next_letter
            if len(next_letter_key) > self._order:
                next_letter_key = next_letter_key[1:]
        return name

    def make_name(self, exclude_real_names = True, exclude_history = True, add_to_history = True,
                  n_candidates = DEFAULT_N_CANDIDATES, pref_candidate = AVG, max_attempts = DEFAULT_MAX_ATTEMPTS, validation_func = None):
        ''' Creates and returns a name,
            or returns an empty string if name creation fails.
            INPUTS:
            exclude_real_names: bool, prevents the creation of a name that's
                                already in this NameSet if True.
            exclude_history:    bool, prevents the creation of a name already in
                                this NameSet's history if True.
            add_to_history:     bool, adds the created name to this NameSet's
                                history if True.
            n_candidates:       int, number of name candidates to create.
                                The best one (as determined by pref_candidate)
                                is  returned.
            pref_candidate:     The method used to pick the preferred name
                                candidate. Possible values:
                                MIN (0): Picks the candidate with the lowest
                                         value according to this
                                         NameSet's name_len_func.
                                MAX (1): Picks the candidate with the highest
                                         value according to this
                                         NameSet's name_len_func.
                                AVG (2): Picks the candidate that best agrees
                                         with the average name length of
                                         this NameSet's training data,
                                         as measured by the name_len_func.
            max_attempts:       int, the maximum number of attempts
                                (per name candidate) to make a valid name.
            validation_func:    function or None, used to weed out invalid name
                                candidates. Must take a single string as input
                                and return True if it's a valid name,
                                False otherwise.'''

        if validation_func is None:
            validation_func = _PASS_EVERYTHING
        
        name_candidates = []
        for i in range(n_candidates):
            n_attempts = 0
            while n_attempts < max_attempts:
                name = self._make_name_raw()
                name_valid = bool(name) \
                             and validation_func(name) \
                             and not (exclude_real_names and name in self) \
                             and not (exclude_history and name in self._history) \
                             and is_clean(name, banned_words)
                if name_valid:
                    name_candidates.append(name)
                    break
                n_attempts += 1

        if not name_candidates:     # give up if there are no valid candidates
            return ''

        if pref_candidate == AVG:
            # percent error of the length of the name from the average length of all names
            sort_key = lambda name: abs(self._name_len_func(name) - self._avg_name_len) / self._avg_name_len 
        elif pref_candidate in (MIN, MAX):
            sort_key = self._name_len_func
        else:
            raise ValueError(f'make_name got an unexpected value for pref_candidate: {pref_candidate}')

        name_candidates.sort(key = sort_key, reverse = pref_candidate == MAX)
        name = name_candidates[0]
        if add_to_history:
            self.add_to_history(name)
        return name

class _NameSetIterator():
    def __init__(self, name_set):
        self.name_set = name_set
        self.index = 0

    def __next__(self):
        if self.index < len(self.name_set._names):
            result = self.name_set[self.index]
            self.index += 1
            return result
        else:
            raise StopIteration

'=================================================================== User functions =========================================================='

def make_name_set(names, order = DEFAULT_ORDER, name_len_func = DEFAULT_NAME_LEN_FUNC, clean_up = True):   # if changing deefault clean_up, also change in sample
    ''' Creates and returns a NameSet object
        with the input names as training data.
        INPUTS:
        names:          Any collection of names, a NameSet,
                        or the name of a file where names are stored.
        order:          int, the order of the Markov chains that will be used
                        to create random names.
                        I.E. how many letters are used for matching.
        name_len_func:  A function used to quantify the length, complexity, or
                        any other interesting property of the NameSet's names.
                        Must take a single string as input and return a
                        numerical value.
        clean_up:       bool, determines if the names will be cleaned of messy
                        data. If True, names will have any non-alphanumeric
                        symbols removed from the start and end of the name,
                        and blank names will be removed.'''
    if type(names) is str:
        names = get_names_from_file(names)
    if clean_up:
        names = clean(names)
    return NameSet(names, order = order, name_len_func = name_len_func)

def get_names_from_file(file_name):
    ''' Takes a file name as a string, with or without a file extension,
        and returns a list of names stored in that file.
        The file should be a text file with one name on each line.
        If no file extension is included,
        this function assumes the extension is .txt'''
    def get_names(file_name, encoding):
        with open(file_name, 'r', encoding = encoding) as f:
            names = [line.strip('\n\r\t') for line in f.readlines()]    # get rid of any newline, carriage return, and tab characters
        return names

    if '.' not in file_name:                                            # if user forgot to include file extension
        file_name += '.txt'                                             # assume it's a text file

    try:
        names = get_names(file_name, 'utf-8')                           # use utf-8 encoding so that unicode characters are read properly.
    except UnicodeDecodeError:                                          # if the file wasn't encoded in UTF-8, fall back to latin-1
        names = get_names(file_name, 'latin-1')                         # This is an easy mistake to make if saving from excel
        warnings.warn('Failed to load Unicode text. Falling back to latin-1 encoding. Some symbols may not be shown properly.', category = UnicodeWarning, stacklevel = 2)
    except FileNotFoundError:
        names = get_built_in_names(file_name)
    return names

def get_built_in_names(file_name):
    ''' Gets names from a text file that was pre-packaged with this module'''
    file_name = f'{_BUILTIN_NAMES_FOLDER}/{file_name}'
    if not file_name.endswith('.txt'):
        file_name += '.txt'
    name_bytes = pkgutil.get_data(__name__, file_name)
    names = name_bytes.decode('utf-8').splitlines()                     # built-in name data will always be in utf-8 format
    return [n.strip('\n\r\t') for n in names]                           # get rid of any newline, carriage return, and tab characters

def clean(names):
    ''' Cleans extra symbols from the start or end of the names,
        and removes blank names.
        names can be any collection of names, including a NameSet.
        Returns a new list. The input object is not modified.'''
    return clean_blanks(clean_extra_symbols(names))

def clean_blanks(names, blank_names = []):
    ''' Removes empty names and names that consist
        only of non-alphanumeric characters.
        Also removes any of the names in the input blank_names list.
        names can be any collection of names, including a NameSet.
        Returns a new list. The input object is not modified.'''
    return [n for n in names if strip_non_alnum(n) and n not in blank_names]

def clean_extra_symbols(names):
    ''' Removes non-alphanumeric characters from the beginning and end of each
        name, in case the data source put extraneous symbols in to denote
        special meaning (like wikipedia sometimes does).
        names can be any collection of names, including a NameSet.
        Returns a new list. The input object is not modified.'''
    return [strip_non_alnum(n) for n in names]

def strip_non_alnum(string):
    ''' Strips any non-alphanumeric characters from the beginning
        and end of the string.
        Doesn't touch non-alphanumeric characters surrounded by
        alphanumeric characters.
        Ex: '? Test-string 2!' becomes 'Test-string 2' '''
    strip_chars = ''.join([char for char in string if not char.isalnum()])
    return string.strip(strip_chars)

def estimate_syllables(name):
    ''' Estimates the number of syllables in the input name.
        Works by counting alternations between consonants and vowels.
        Only an estimate, not necessarily accurate.
        For reference, 'antidisestablishmentarianism' is 12 syllables
        and this function estimates it as 10.
        'The quick brown fox jumped over the lazy dog.'
        is 11 and this function estimates it as 12.'''
    if not name:
        return 0

    consonants = list("bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ'")  # also treats an apostrophy as a consonant
    vowels = list('aeiouyAEIOUY')
    new_syllable_chars = list(' -')
    add_syllable_chars = {'1': 1, '2':1, '3':1, '4':1, '5':1, '6':1, '7':2, '8':1, '9':1, '0':2}

    n_syllables = 0         # a syllable is added when the syllable is finished
    syllable_section = 1    # 1: first batch of consonants, 2: batch of vowels, 3: last batch of consonants
    for letter in name:
        if letter in add_syllable_chars:
            n_syllables += add_syllable_chars[letter]

        elif letter in new_syllable_chars:
            n_syllables += 1
            syllable_section = 1

        elif letter in vowels:
            if syllable_section == 1:
                syllable_section = 2
            elif syllable_section == 3:
                n_syllables += 1
                syllable_section = 2    # don't start over with a new run of consonants

        elif letter in consonants:
            if syllable_section == 2:
                syllable_section = 3

    if name[-1] not in new_syllable_chars and name[-1] not in add_syllable_chars:
        n_syllables += 1    # add a syllable because the current syllable is now finished and hasn't yet been counted

    return n_syllables

def _make_name_set_for_user_testing(names, **kwargs):
    if type(names) is NameSet:
        if 'order' in kwargs and kwargs['order'] != names.get_order():      # message if kwargs conflicts with NameSet attributes
            print(f'Input NameSet has order {names.get_order()}, but input kwargs specified order {kwargs["order"]}. Using {kwargs["order"]}.')
        elif names.get_order() != DEFAULT_ORDER and 'order' not in kwargs:  # message if NameSet attributes conflict with defaults, only if not specified in kwargs
            print(f'Using the input NameSet\'s order {names.get_order()} instead of the default order {DEFAULT_ORDER}.')
        order = kwargs.pop('order', names.get_order())

        if 'name_len_func' in kwargs and kwargs['name_len_func'] is not names.get_name_len_func():      # message if kwargs conflicts with NameSet attributes
            print(f'Input NameSet has name_len_func {names.get_name_len_func()}, but input kwargs specified name_len_func {kwargs["name_len_func"]}. Using {kwargs["name_len_func"]}.')
        elif names.get_name_len_func() is not DEFAULT_NAME_LEN_FUNC and 'name_len_func' not in kwargs:  # message if NameSet attributes conflict with defaults, only if not specified in kwargs
            print(f'Using the input NameSet\'s name_len_func {names.get_name_len_func()} instead of the default name_len_func {DEFAULT_NAME_LEN_FUNC}.')
        name_len_func = kwargs.pop('name_len_func', names.get_name_len_func())

    else:
        order = kwargs.pop('order', DEFAULT_ORDER)
        name_len_func = kwargs.pop('name_len_func', DEFAULT_NAME_LEN_FUNC)

    clean_up = kwargs.pop('clean_up', True)     # The default value for 'clean_up' is based on the default in make_name_set
    name_set = make_name_set(names, order, name_len_func, clean_up)

    if type(names) is NameSet:
        if list(names) != list(name_set):
            print('These names were generated with a cleaned-up version of your input NameSet.\n'
                  'To suppress this behavior, use the keyword argument clean_up = False')
        history = names.get_history()
        if history:
            print(f'The input NameSet already has {len(history)} names in its history.')
            name_set.add_to_history(history)    # stay faithful to the input NameSet

    return name_set, kwargs                     # return the kwargs so the calling function doesn't have to get rid of the kwargs that were popped

def sample(names, n = 20, **kwargs):
    ''' Prints a sample of n names based on the input collection of names.
        Uses the input **kwargs in make_name_set and in calls to
        NameSet.make_name.
        The intent of this function is to get a quick idea of how
        different inputs affect the final result.
        It is not intended for use in production code.
        Values specified in **kwargs are prioritized,
        followed by attributes of the input NameSet (if names is a NameSet),
        followed by default values.
        This function operates on a copy of names,
        so the input list, set, or NameSet of names will not be modified.
        
        INPUTS:
        names:    Any collection of names, a NameSet, or the name of a
                  file where names are stored.
        n:        int, the number of samples to print.
        **kwargs: Any keyword arguments that are accepted by make_name_set or
                  NameSet.make_name'''

    name_set, kwargs = _make_name_set_for_user_testing(names, **kwargs)
    for i in range(n):
        print(name_set.make_name(**kwargs))

def stress_test(names, **kwargs):
    ''' Generates names until NameSet.make_name fails once, then prints
        the number of names generated compared to the number
        of names in the training data.
        Uses the input **kwargs in make_name_set and in calls to
        NameSet.make_name.
        It can take several seconds or minutes before make_name fails,
        if it ever does.
        Cancelling this function early will still display the test results.
        The intent of this function is to judge how many names can be
        generated from the inputs before no more can be made without repeats.
        I.e. to see how long it takes to fill up a NameSet's history.
        It is not intended for use in production code.
        Values specified in **kwargs are prioritized,
        followed by attributes of the input NameSet (if names is a NameSet),
        followed by default values.
        This function operates on a copy of names,
        so the input list, set, or NameSet of names will not be modified.
        
        INPUTS:
        names:    Any collection of names, a NameSet, or the name of a
                  file where names are stored.
        **kwargs: Any keyword arguments that are accepted by make_name_set or
                  NameSet.make_name
                  Note: Setting add_to_history = False will mess up unique
                  name reporting.'''
    name_set, kwargs = _make_name_set_for_user_testing(names, **kwargs)
    if name_set.get_history():
        print('The test will run on a copy of the NameSet with no history.')
    name_set.clear_history()

    if len(name_set) == 0:                      # insanity check
        print('Cannot generate any names from an empty NameSet.')
        return

    n_training = len(name_set)
    n_made = 0
    try:
        while name_set.make_name(**kwargs):     # make names until there's a failure
            n_made += 1
    except KeyboardInterrupt:
        print('The test was cancelled before a failure occurred.')
    n_unique = len(name_set.get_history())

    if not kwargs.get('add_to_history', True):
        print('Info on unique generated names will not be accurate'
              '\nbecause add_to_history is False.')
    print(f'Training names: {n_training}')
    print(f'Unique generated names: {n_unique}')
    print(f'Total generated names: {n_made}')
    print(f'Generated names per training name: {round(n_made/n_training, 1)}')
    print(f'Percent of generated names that are unique: {round(100*n_unique/n_made, 1) if n_made else 0}%')

def is_clean(name, banned_words):
    ''' Returns True if the name is clean,
        i.e. it does not contain any banned words.
        Returns False if there is a banned word in the name.
        Not case sensitive.
        This function is called in NameSet.make_name with the module-level
        banned_words set to make sure a name containing a banned word is
        not generated.

        INPUTS:
        name:         A string.
        banned_words: A collection of words that are not allowed in name.'''
    casefolded_name = name.casefold()
    for word in banned_words:   # avoid using get_banned_words for performance reasons. No need to make a copy of the banned_words list for every name candidate
        if word.casefold() in casefolded_name:
            return False
    else:
        return True

def set_banned_words(words):
    ''' Sets this module's banned_words set to be the input collection of words.
        Not case sensitive.'''
    global banned_words
    if type(words) is str:
        raise TypeError('set_banned_words does not accept a str as input.')
    banned_words = set(words)

def add_banned_words(words):
    ''' Adds the input collection of words to this module's banned_words set.
        Not case sensitive.'''
    global banned_words
    if type(words) is str:
        raise TypeError('add_banned_words does not accept a str as input.')
    banned_words |= set(words)

def get_banned_words():
    ''' Returns a copy of this module's banned_words set.'''
    return {*banned_words}

















