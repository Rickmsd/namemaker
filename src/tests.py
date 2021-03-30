''' unit tests for name generator'''

import unittest
import copy
import random
import namemaker

test_names_1 = ['name 1', 'name2', 'name3', 'name4']     # one different length name to test that _avg_name_len is updated correctly
test_names_2 = ['name3', 'name4', 'name5']
test_names_3 = ['name1']*2 + ['name2']*4
test_names_4 = ['name2']*2 + ['name3']*3

def copy_checks(test_case, name_set, copy_set):
    test_case.assertIsNot(name_set, copy_set)
    test_case.assertIsNot(name_set._names, copy_set._names)
    test_case.assertIsNot(name_set._names_set, copy_set._names_set)
    test_case.assertIsNot(name_set._markov_dict, copy_set._markov_dict)
    test_case.assertIsNot(name_set._history, copy_set._history)

    test_case.assertEqual(name_set._names, copy_set._names)
    test_case.assertEqual(name_set._names_set, copy_set._names_set)
    test_case.assertEqual(name_set._markov_dict, copy_set._markov_dict)
    test_case.assertEqual(name_set._history, copy_set._history)
    test_case.assertEqual(name_set._order, copy_set._order)
    test_case.assertEqual(name_set._avg_name_len, copy_set._avg_name_len)
    test_case.assertIs(name_set._name_len_func, copy_set._name_len_func)

    for key, letters in name_set._markov_dict.items():  # make sure every list of letters in the markov_dict is its own object, not the same list object as the original
        test_case.assertIsNot(letters, copy_set._markov_dict[key])

def avg_len(names, func):
    return sum([func(name) for name in names]) / len(names)

def sneaky_iadd(item_1, item_2):
    item_1 += item_2

def sneaky_isub(item_1, item_2):
    item_1 -= item_2

def sneaky_ior(item_1, item_2):
    item_1 |= item_2

def sneaky_iand(item_1, item_2):
    item_1 &= item_2

class NameSetBookkeepingTests(unittest.TestCase):
    def setUp(self):
        self.name_set = namemaker.NameSet(test_names_1[:])
        self.name_set.add_to_history(test_names_1[:])   # give the NameSets some hisory to make sure that's handled correctly, too
        self.n3 = namemaker.NameSet(test_names_3[:])
        self.n3.add_to_history(test_names_3[:])

    def test_init(self):
        self.assertEqual(self.name_set._names, test_names_1[:])
        self.assertEqual(self.name_set._names_set, set(test_names_1))
        self.assertIs(self.name_set._name_len_func, namemaker.DEFAULT_NAME_LEN_FUNC)
        self.assertEqual(self.name_set._avg_name_len, avg_len(self.name_set, self.name_set._name_len_func))
        self.assertEqual(self.name_set._order, namemaker.DEFAULT_ORDER)

        self.assertEqual(self.n3._names, test_names_3[:])       # test that the names are set correctly even when there are duplicates in the input list
        self.assertEqual(self.n3._names_set, set(test_names_3))

    def test_copy(self):
        ''' tests NameSet.copy'''
        copy_set = self.name_set.copy()
        copy_checks(self, self.name_set, copy_set)
        copy_set_3 = self.n3.copy()
        copy_checks(self, self.n3, copy_set_3)

    def test_copy_copy(self):
        ''' tests copy.copy on a NameSet'''
        self.assertWarns(namemaker.CopyWarning, copy.copy, self.name_set)
        copy_set = copy.copy(self.name_set)
        copy_checks(self, self.name_set, copy_set)
        copy_set_3 = copy.copy(self.n3)
        copy_checks(self, self.n3, copy_set_3)

    def test_copy_deepcopy(self):
        ''' tests copy.deepcopy on a NameSet'''
        copy_set = copy.deepcopy(self.name_set)
        copy_set = copy.deepcopy(self.name_set)
        copy_checks(self, self.name_set, copy_set)
        copy_set_3 = copy.deepcopy(self.n3)
        copy_checks(self, self.n3, copy_set_3)

    def test_eq(self):
        ''' tests the == operator for NameSets'''
        other_name_set = self.name_set.copy()
        self.assertTrue(self.name_set == other_name_set)
        self.assertTrue(other_name_set == self.name_set)
        self.assertFalse(self.name_set != other_name_set)
        self.assertFalse(self.name_set == test_names_1[:])

        # test that changing any attribute of the NameSet causes them to be unequal

        other_name_set = self.name_set.copy()
        other_name_set._order += 1
        self.assertFalse(self.name_set == other_name_set)

        other_name_set = self.name_set.copy()
        other_name_set._name_len_func = lambda name: 5
        self.assertFalse(self.name_set == other_name_set)

        other_name_set = self.name_set.copy()
        other_name_set._avg_name_len += 1
        self.assertFalse(self.name_set == other_name_set)

        other_name_set = self.name_set.copy()
        other_name_set._names.append('hey')
        self.assertFalse(self.name_set == other_name_set)

        other_name_set = self.name_set.copy()
        other_name_set._names_set.add('hey')
        self.assertFalse(self.name_set == other_name_set)

        other_name_set = self.name_set.copy()
        other_name_set._markov_dict['n'].append('n')        # make sure that changing even one letter in the markov_dict causes the NameSets to be unequal
        self.assertFalse(self.name_set == other_name_set)

        other_name_set = self.name_set.copy()
        other_name_set.clear_history()
        self.assertFalse(self.name_set == other_name_set)

    def test_iteration(self):
        unpacked_list = [*self.name_set]
        self.assertEqual(unpacked_list, test_names_1[:])
        self.assertEqual(list(self.name_set), test_names_1[:])

        i = 0
        for name in self.name_set:
            self.assertEqual(name, test_names_1[i])
            i += 1

    def test_getitem(self):
        self.assertEqual(self.name_set[0], test_names_1[0])
        self.assertEqual(self.name_set[-1], test_names_1[-1])

    @unittest.expectedFailure
    def test_setitem(self):
        self.name_set[0] = 'hey'

    def test_len(self):
        self.assertEqual(len(self.name_set), len(test_names_1))

    def test_contains(self):
        self.assertTrue('name 1' in self.name_set)
        self.assertTrue('fskhk' not in self.name_set)
        self.assertFalse('kfhkslfh' in self.name_set)
        self.assertFalse(5 in self.name_set)

    def test_wrong_order(self):
        self.assertRaises(ValueError, namemaker.NameSet, test_names_1[:], order = 1.5)
        self.assertRaises(ValueError, namemaker.NameSet, test_names_1[:], order = -1)
        namemaker.NameSet(test_names_1[:], order = 0)   # setting the order to 0 should work just fine

class CoreFunctionalityTests(unittest.TestCase):
    def test_markov_dict(self):
        n = namemaker.NameSet(['name 1', 'name2'], order = 2)
        expected_dict = {'': ['n', 'n'],
                         'n': ['a', 'a'],
                         'na': ['m', 'm'],
                         'am': ['e', 'e'],
                         'me': [' ', '2'],
                         'e ': ['1'],
                         ' 1': [namemaker._END],
                         'e2': [namemaker._END]}
        self.assertEqual(n._markov_dict, expected_dict)

        n = namemaker.NameSet(['name 1', 'name2'], order = 3)
        expected_dict = {'': ['n', 'n'],
                         'n': ['a', 'a'],
                         'na': ['m', 'm'],
                         'nam': ['e', 'e'],
                         'ame': [' ', '2'],
                         'me ': ['1'],
                         'e 1': [namemaker._END],
                         'me2': [namemaker._END]}
        self.assertEqual(n._markov_dict, expected_dict)

    def test_exclude_real_names(self):
        names = ['name 1', 'name2']
        n = namemaker.NameSet(names)
        result_1 = n.make_name()
        result_2 = n.make_name(exclude_real_names = False)
        self.assertEqual(result_1, '')
        self.assertIn(result_2, names)

    def test_history(self):
        names = ['name1']
        n = namemaker.NameSet(names)
        for i in range(5):
            result = n.make_name(exclude_real_names = False, add_to_history = False)
            self.assertEqual(result, names[0])
        self.assertEqual(n._history, set())

        for i in range(5):
            result = n.make_name(exclude_real_names = False, exclude_history = False)
            self.assertEqual(result, names[0])
        self.assertEqual(n._history, set(names))

        result = n.make_name(exclude_real_names = False)    # should result in '' because exclude_history is True by default
        self.assertEqual(result, '')

    def test_validation_func(self):
        n = namemaker.NameSet(test_names_1[:])
        v = lambda name: len(name) == 5
        n_valid_names = 0
        for t in test_names_1:
            result = n.make_name(exclude_real_names = False, validation_func = v)
            if result:
                n_valid_names += 1
        self.assertEqual(n_valid_names, len(test_names_1) - 1)  # one of the names in test_names_1 is 6 characters long

        result = n.make_name(exclude_real_names = False, exclude_history = False, validation_func = lambda name: False)
        self.assertEqual(result, '')

    def test_banned_words(self):
        namemaker.banned_words = {'name'}
        names = ['NAME1', 'name2', ' NaMe 3 ']
        n = namemaker.NameSet(names)
        result = n.make_name(exclude_real_names = False)
        self.assertEqual(result, '')

        namemaker.banned_words = {'NAME'}           # make sure banned words are case insensitive
        names = ['NAME1', 'name2', ' NaMe 3 ']
        n = namemaker.NameSet(names)
        result = n.make_name(exclude_real_names = False)
        self.assertEqual(result, '')

        namemaker.banned_words = set()              # clean up so banned_words it doesn't affect other tests

    def test_candidate_selection(self):
        ''' make sure name candidate selection using MIN, MAX, and AVG works properly'''
        n = namemaker.NameSet(['hey', 'hi', 'hello'])
        short_result = n.make_name(exclude_real_names = False, add_to_history = False, n_candidates = 20, pref_candidate = namemaker.MIN)
        med_result = n.make_name(exclude_real_names = False, add_to_history = False, n_candidates = 20, pref_candidate = namemaker.AVG)
        long_result = n.make_name(exclude_real_names = False, add_to_history = False, n_candidates = 20, pref_candidate = namemaker.MAX)

        self.assertEqual(short_result, 'hi')
        self.assertEqual(med_result, 'hey')
        self.assertEqual(long_result, 'hello')

class NameSetManipulationTests(unittest.TestCase):
    def setUp(self):
        self.n1 = namemaker.NameSet(test_names_1[:])
        self.n2 = namemaker.NameSet(test_names_2[:])
        self.n3 = namemaker.NameSet(test_names_3[:])
        self.n4 = namemaker.NameSet(test_names_4[:])

        self.n1.add_to_history(test_names_1[:])     # give the NameSets some hisory to make sure that's handled correctly, too
        self.n2.add_to_history(test_names_2[:])
        self.n3.add_to_history(test_names_3[:])
        self.n4.add_to_history(test_names_4[:])

    ## Addition tests

    def test_basic_add(self):
        ''' test that addition results in the correct names being present,
            for a variety of different types of name collections'''
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1 + type_(test_names_2)
            self.assertCountEqual(list(result_set), test_names_1 + test_names_2)    # make sure the result is added correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after addition
            self.assertEqual(result_set._history, set())                            # make sure the result of the addition doesn't have any history
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_basic_iadd(self):
        ''' test that addition in place results in the correct names being present,
            for a variety of different types of name collections'''
        n1_history = self.n1._history
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1.copy()
            result_set += type_(test_names_2)
            self.assertCountEqual(list(result_set), test_names_1 + test_names_2)    # make sure the result is added correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after addition
            self.assertEqual(n1_history, result_set._history)                       # make sure the set being added to still has its history unaltered
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_add_nothing(self):
        ''' Makes sure the NameSet can handle addition of an empty list and still have the right names'''
        result = self.n1 + []
        desired_result = self.n1.copy()
        desired_result.clear_history()                      # the result of addition should have no history
        self.assertEqual(list(result), test_names_1[:])
        self.assertTrue(result == desired_result)           # make sure the empty names didn't change anything about the NameSet

        # do the same for iadd
        desired_result._history = {*self.n1._history}       # make sure n1 keeps its history in tact
        self.n1 += []
        self.assertEqual(list(self.n1), test_names_1[:])
        self.assertTrue(self.n1 == desired_result)          # make sure the empty names didn't change anything about the NameSet

    def test_add_to_nothing(self):
        ''' Makes sure an empty NameSet can be added to'''
        empty_name_set = namemaker.NameSet([])
        result = empty_name_set + self.n1
        desired_result = self.n1.copy()
        desired_result.clear_history()                      # the result of addition should have no history
        self.assertEqual(list(result), test_names_1[:])
        self.assertTrue(result == desired_result)           # make sure the empty names didn't change anything about the NameSet

        # do the same for iadd
        empty_name_set += self.n1
        self.assertEqual(list(empty_name_set), test_names_1[:])
        self.assertTrue(empty_name_set == desired_result)   # make sure the empty names didn't change anything about the NameSet

    def test_add_identity(self):
        ''' test that references are all to the correct objects after addition'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by addition
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()

        result_set = self.n1 + self.n2
        
        self.assertIsNot(result_set, self.n1)       # make sure a new NameSet is returned
        self.assertIsNot(result_set, self.n2)
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the addition
        copy_checks(self, self.n2, n2_copy)

    def test_iadd_identity(self):
        ''' test that references are all to the correct objects after addition in place'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by addition
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()
        result_set = self.n1.copy()
        also_result_set = result_set

        result_set += self.n2

        self.assertIs(result_set, also_result_set)  # make sure the name set that was added to is still the same object that it was at the start
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the addition
        copy_checks(self, self.n2, n2_copy)

    def test_add_with_duplicates(self):
        ''' tests adding when the name sets already have duplicated names in them'''
        result_set = self.n3 + self.n4
        self.assertEqual(result_set._names, test_names_3 + test_names_4)
        self.assertEqual(result_set._names_set, set(test_names_3 + test_names_4))

    def test_iadd_with_duplicates(self):
        self.n3 += self.n4
        result_set = self.n3
        self.assertEqual(result_set._names, test_names_3 + test_names_4)
        self.assertEqual(result_set._names_set, set(test_names_3 + test_names_4))

    def test_add_different_order(self):
        ''' make sure addition of two NameSets of different order results in a warning,
            and that the result has the order of the first NameSet'''
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.assertWarns(namemaker.OrderWarning, lambda: self.n1 + self.n2)
        result_set = self.n1 + self.n2
        self.assertEqual(result_set._order, self.n1._order)

        # do the same test for iadd
        self.assertWarns(namemaker.OrderWarning, sneaky_iadd, self.n1, self.n2)    # make sure a warning happens when adding n2 to n1 with a different order
        self.assertEqual(namemaker.DEFAULT_ORDER, self.n1._order)                   # make sure n1's order wasn't changed
        ## self.assertEqual(list(self.n1), test_names_1 + test_names_2)        # for my own sanity to know n1 was modified

    def test_add_different_name_len_func(self):
        ''' make sure addition of two NameSets of different name_len_func results in a warning,
            and that the result has the name_len_func of the first NameSet'''
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        self.assertWarns(namemaker.NameLenWarning, lambda: self.n1 + self.n2)
        result_set = self.n1 + self.n2
        self.assertIs(result_set._name_len_func, self.n1._name_len_func)

        # do the same test for iadd
        self.assertWarns(namemaker.NameLenWarning, sneaky_iadd, self.n1, self.n2)  # make sure a warning happens when adding n2 to n1 with a different name_len_func
        self.assertIs(namemaker.DEFAULT_NAME_LEN_FUNC, self.n1._name_len_func)      # make sure n1's name_len_func wasn't changed

    def test_add_string_error(self):
        ''' make sure an exception is raised when trying to add a string to a NameSet'''
        self.assertRaises(TypeError, lambda: self.n1 + 'hi')
        self.assertRaises(TypeError, sneaky_iadd, self.n1, 'hi')


    ## Subtraction tests

    def test_basic_sub(self):
        ''' test that subtraction results in the correct names being present,
            for a variety of different types of name collections'''
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1 - type_(test_names_2)
            self.assertCountEqual(list(result_set), ['name 1', 'name2'])             # make sure the result is sutracted correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after subtraction
            self.assertEqual(result_set._history, set())                            # make sure the result of the subtraction doesn't have any history
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_basic_isub(self):
        ''' test that subtraction in place results in the correct names being present,
            for a variety of different types of name collections'''
        n1_history = self.n1._history
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1.copy()
            result_set -= type_(test_names_2)
            self.assertCountEqual(list(result_set), ['name 1', 'name2'])             # make sure the result is subtracted correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after subtraction
            self.assertEqual(n1_history, result_set._history)                       # make sure the set being subtracted from still has its history unaltered
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_sub_nothing(self):
        ''' Makes sure the NameSet can handle subtraction of an empty list and still have the right names'''
        result = self.n1 - []
        desired_result = self.n1.copy()
        desired_result.clear_history()                      # the result of subtraction should have no history
        self.assertEqual(list(result), test_names_1[:])
        self.assertTrue(result == desired_result)           # make sure the empty names didn't change anything about the NameSet

        # do the same for iadd
        desired_result._history = {*self.n1._history}       # make sure n1 keeps its history in tact
        self.n1 -= []
        self.assertEqual(list(self.n1), test_names_1[:])
        self.assertTrue(self.n1 == desired_result)          # make sure the empty names didn't change anything about the NameSet

    def test_sub_from_nothing(self):
        ''' Makes sure an empty NameSet can be subtracted from'''
        empty_name_set = namemaker.NameSet([])
        result = empty_name_set - self.n1
        desired_result = empty_name_set.copy()
        desired_result.clear_history()                      # the result of subtraction should have no history
        self.assertEqual(list(result), [])
        self.assertTrue(result == desired_result)           # make sure the empty names didn't change anything about the NameSet

        # do the same for isub
        empty_name_set -= self.n1
        self.assertEqual(list(empty_name_set), [])
        self.assertTrue(empty_name_set == desired_result)   # make sure the empty names didn't change anything about the NameSet

    def test_sub_identity(self):
        ''' test that references are all to the correct objects after subtraction'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by subtraction
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()

        result_set = self.n1 - self.n2
        
        self.assertIsNot(result_set, self.n1)       # make sure a new NameSet is returned
        self.assertIsNot(result_set, self.n2)
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the subtraction
        copy_checks(self, self.n2, n2_copy)

    def test_isub_identity(self):
        ''' test that references are all to the correct objects after subtraction in place'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by subtraction
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()
        result_set = self.n1.copy()
        also_result_set = result_set

        result_set -= self.n2

        self.assertIs(result_set, also_result_set)  # make sure the name set that was subtracted from is still the same object that it was at the start
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the subtraction
        copy_checks(self, self.n2, n2_copy)

    def test_sub_with_duplicates(self):
        ''' tests subtraction when the name sets already have duplicated names in them'''
        result_set = self.n3 - self.n4
        desired_result = ['name1']*2 + ['name2']*2  # test_names_3 with two 'name2's removed
        self.assertEqual(result_set._names, desired_result)
        self.assertEqual(result_set._names_set, set(desired_result))

    def test_isub_with_duplicates(self):
        self.n3 -= self.n4
        result_set = self.n3
        desired_result = ['name1']*2 + ['name2']*2  # test_names_3 with two 'name2's removed
        self.assertEqual(result_set._names, desired_result)
        self.assertEqual(result_set._names_set, set(desired_result))

    def test_sub_different_order(self):
        ''' make sure subtraction of two NameSets of different order results in a warning,
            and that the result has the order of the first NameSet'''
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.assertWarns(namemaker.OrderWarning, lambda: self.n1 - self.n2)
        result_set = self.n1 - self.n2
        self.assertEqual(result_set._order, self.n1._order)

        # do the same test for isub
        self.assertWarns(namemaker.OrderWarning, sneaky_isub, self.n1, self.n2)    # make sure a warning happens when subtracting n2 from n1 with a different order
        self.assertEqual(namemaker.DEFAULT_ORDER, self.n1._order)                   # make sure n1's order wasn't changed

    def test_sub_different_name_len_func(self):
        ''' make sure subtraction of two NameSets of different name_len_func results in a warning,
            and that the result has the name_len_func of the first NameSet'''
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        self.assertWarns(namemaker.NameLenWarning, lambda: self.n1 - self.n2)
        result_set = self.n1 - self.n2
        self.assertIs(result_set._name_len_func, self.n1._name_len_func)

        # do the same test for isub
        self.assertWarns(namemaker.NameLenWarning, sneaky_isub, self.n1, self.n2)  # make sure a warning happens when subtracting n2 from n1 with a different name_len_func
        self.assertIs(namemaker.DEFAULT_NAME_LEN_FUNC, self.n1._name_len_func)      # make sure n1's name_len_func wasn't changed

    def test_sub_string_error(self):
        ''' make sure an exception is raised when trying to subtract a string from a NameSet'''
        self.assertRaises(TypeError, lambda: self.n1 - 'hi')
        self.assertRaises(TypeError, sneaky_isub, self.n1, 'hi')


    ## Union tests

    def test_basic_or(self):
        ''' test that union results in the correct names being present,
            for a variety of different types of name collections'''
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1 | type_(test_names_2)
            self.assertCountEqual(list(result_set), set(test_names_1 + test_names_2))   # make sure the result is unioned correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after union
            self.assertEqual(result_set._history, set())                            # make sure the result of the union doesn't have any history
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_basic_ior(self):
        ''' test that union in place results in the correct names being present,
            for a variety of different types of name collections'''
        n1_history = self.n1._history
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1.copy()
            result_set |= type_(test_names_2)
            self.assertCountEqual(list(result_set), set(test_names_1 + test_names_2))   # make sure the result is unioned correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after union
            self.assertEqual(n1_history, result_set._history)                       # make sure the set being unioned with still has its history unaltered
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_or_nothing(self):
        ''' Makes sure the NameSet can handle union with an empty list and still have the right names'''
        result = self.n1 | []
        desired_result = self.n1.copy()
        desired_result.clear_history()                      # the result of union should have no history
        self.assertEqual(list(result), test_names_1[:])
        self.assertTrue(result == desired_result)           # make sure the empty names didn't change anything about the NameSet

        # do the same for iadd
        desired_result._history = {*self.n1._history}       # make sure n1 keeps its history in tact
        self.n1 |= []
        self.assertEqual(list(self.n1), test_names_1[:])
        self.assertTrue(self.n1 == desired_result)          # make sure the empty names didn't change anything about the NameSet

    def test_or_to_nothing(self):
        ''' Makes sure an empty NameSet can be unioned with'''
        empty_name_set = namemaker.NameSet([])
        result = empty_name_set | self.n1
        desired_result = self.n1.copy()
        desired_result.clear_history()                      # the result of union should have no history
        self.assertEqual(list(result), test_names_1[:])
        self.assertTrue(result == desired_result)           # make sure the empty names didn't change anything about the NameSet

        # do the same for ior
        empty_name_set |= self.n1
        self.assertEqual(list(empty_name_set), test_names_1[:])
        self.assertTrue(empty_name_set == desired_result)   # make sure the empty names didn't change anything about the NameSet

    def test_or_identity(self):
        ''' test that references are all to the correct objects after union'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by union
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()

        result_set = self.n1 | self.n2
        
        self.assertIsNot(result_set, self.n1)       # make sure a new NameSet is returned
        self.assertIsNot(result_set, self.n2)
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the union
        copy_checks(self, self.n2, n2_copy)

    def test_ior_identity(self):
        ''' test that references are all to the correct objects after union in place'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by union
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()
        result_set = self.n1.copy()
        also_result_set = result_set

        result_set |= self.n2

        self.assertIs(result_set, also_result_set)  # make sure the name set that was unioned with is still the same object that it was at the start
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the union
        copy_checks(self, self.n2, n2_copy)

    def test_or_with_duplicates(self):
        ''' tests union when the name sets already have duplicated names in them'''
        result_set = self.n3 | self.n4
        desired_result = ['name1', 'name2', 'name3']    # test_names_3 | test_names_4
        self.assertEqual(result_set._names, desired_result)
        self.assertEqual(result_set._names_set, set(desired_result))

    def test_ior_with_duplicates(self):
        self.n3 |= self.n4
        result_set = self.n3
        desired_result = ['name1', 'name2', 'name3']    # test_names_3 with two 'name2's removed
        self.assertEqual(result_set._names, desired_result)
        self.assertEqual(result_set._names_set, set(desired_result))

    def test_or_different_order(self):
        ''' make sure union of two NameSets of different order results in a warning,
            and that the result has the order of the first NameSet'''
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.assertWarns(namemaker.OrderWarning, lambda: self.n1 | self.n2)
        result_set = self.n1 | self.n2
        self.assertEqual(result_set._order, self.n1._order)

        # do the same test for ior
        self.assertWarns(namemaker.OrderWarning, sneaky_ior, self.n1, self.n2)     # make sure a warning happens when unioning n2 from n1 with a different order
        self.assertEqual(namemaker.DEFAULT_ORDER, self.n1._order)                   # make sure n1's order wasn't changed

    def test_or_different_name_len_func(self):
        ''' make sure union of two NameSets of different name_len_func results in a warning,
            and that the result has the name_len_func of the first NameSet'''
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        self.assertWarns(namemaker.NameLenWarning, lambda: self.n1 | self.n2)
        result_set = self.n1 | self.n2
        self.assertIs(result_set._name_len_func, self.n1._name_len_func)

        # do the same test for ior
        self.assertWarns(namemaker.NameLenWarning, sneaky_ior, self.n1, self.n2)   # make sure a warning happens when unioning n2 from n1 with a different name_len_func
        self.assertIs(namemaker.DEFAULT_NAME_LEN_FUNC, self.n1._name_len_func)      # make sure n1's name_len_func wasn't changed

    def test_or_string_error(self):
        ''' make sure an exception is raised when trying to union a string with a NameSet'''
        self.assertRaises(TypeError, lambda: self.n1 | 'hi')
        self.assertRaises(TypeError, sneaky_ior, self.n1, 'hi')


    ## Intersection tests

    def test_basic_and(self):
        ''' test that intersection results in the correct names being present,
            for a variety of different types of name collections'''
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1 & type_(test_names_2)
            self.assertCountEqual(list(result_set), ['name3', 'name4'])   # make sure the result is intersected correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after intersection
            self.assertEqual(result_set._history, set())                            # make sure the result of the intersection doesn't have any history
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_basic_iand(self):
        ''' test that intersection in place results in the correct names being present,
            for a variety of different types of name collections'''
        n1_history = self.n1._history
        for type_ in (list, set, tuple, namemaker.NameSet):
            result_set = self.n1.copy()
            result_set &= type_(test_names_2)
            self.assertCountEqual(list(result_set), ['name3', 'name4'])   # make sure the result is intersected correctly, but the order of the list doesn't matter
            self.assertEqual(set(result_set._names), result_set._names_set)         # make sure the _names_set is still correct after intersection
            self.assertEqual(n1_history, result_set._history)                       # make sure the set being intersected with still has its history unaltered
            self.assertEqual(result_set._avg_name_len, avg_len(result_set, result_set._name_len_func))

    def test_and_nothing(self):
        ''' Makes sure the NameSet can handle intersection with an empty list and end up empty'''
        result = self.n1 & []
        desired_result = namemaker.NameSet([], order = self.n1._order, name_len_func = self.n1._name_len_func)
        self.assertEqual(list(result), [])
        self.assertTrue(result == desired_result)           # make sure the empty names changed the NameSet into an empty NameSet with the same history

        # do the same for iand
        desired_result._history = {*self.n1._history}       # make sure n1's history is preserved when intersecting in place
        self.n1 &= []
        self.assertEqual(list(self.n1), [])
        self.assertEqual(self.n1._markov_dict, {})
        self.assertTrue(self.n1 == desired_result)          # make sure the empty names changed the NameSet into an empty NameSet with the same history

    def test_and_with_nothing(self):
        ''' Makes sure an empty NameSet can be intersected with'''
        empty_name_set = namemaker.NameSet([])
        result = empty_name_set & self.n1
        desired_result = empty_name_set.copy()
        desired_result.clear_history()                      # the result of intersection should have no history
        self.assertEqual(list(result), [])
        self.assertTrue(result == desired_result)           # make sure the empty names didn't change anything about the NameSet

        # do the same for iand
        empty_name_set &= self.n1
        self.assertEqual(list(empty_name_set), [])
        self.assertTrue(empty_name_set == desired_result)   # make sure the empty names didn't change anything about the NameSet

    def test_and_identity(self):
        ''' test that references are all to the correct objects after intersection'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by intersection
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()

        result_set = self.n1 & self.n2
        
        self.assertIsNot(result_set, self.n1)       # make sure a new NameSet is returned
        self.assertIsNot(result_set, self.n2)
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the intersection
        copy_checks(self, self.n2, n2_copy)

    def test_iand_identity(self):
        ''' test that references are all to the correct objects after intersection in place'''
        self.n1.change_order(namemaker.DEFAULT_ORDER + 1)  # change the order and name_len_func of each NameSet to be sure neither is affected by intersection
        self.n1.change_name_len_func(lambda name: 5)
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        n1_copy = self.n1.copy()
        n2_copy = self.n2.copy()
        result_set = self.n1.copy()
        also_result_set = result_set

        result_set &= self.n2

        self.assertIs(result_set, also_result_set)  # make sure the name set that was intersected with is still the same object that it was at the start
        copy_checks(self, self.n1, n1_copy)         # make sure the name sets were not modified by the intersection
        copy_checks(self, self.n2, n2_copy)

    def test_and_with_duplicates(self):
        ''' tests intersection when the name sets already have duplicated names in them'''
        result_set = self.n3 & self.n4
        desired_result = ['name2']*2    # the overlap of test_names_3 and test_names_4
        self.assertEqual(result_set._names, desired_result)
        self.assertEqual(result_set._names_set, set(desired_result))

    def test_iand_with_duplicates(self):
        self.n3 &= self.n4
        result_set = self.n3
        desired_result = ['name2']*2    # the overlap of test_names_3 and test_names_4
        self.assertEqual(result_set._names, desired_result)
        self.assertEqual(result_set._names_set, set(desired_result))

    def test_and_different_order(self):
        ''' make sure intersection of two NameSets of different order results in a warning,
            and that the result has the order of the first NameSet'''
        self.n2.change_order(namemaker.DEFAULT_ORDER - 1)
        self.assertWarns(namemaker.OrderWarning, lambda: self.n1 & self.n2)
        result_set = self.n1 & self.n2
        self.assertEqual(result_set._order, self.n1._order)

        # do the same test for iand
        self.assertWarns(namemaker.OrderWarning, sneaky_iand, self.n1, self.n2)    # make sure a warning happens when intersecting n2 from n1 with a different order
        self.assertEqual(namemaker.DEFAULT_ORDER, self.n1._order)                   # make sure n1's order wasn't changed

    def test_and_different_name_len_func(self):
        ''' make sure intersection of two NameSets of different name_len_func results in a warning,
            and that the result has the name_len_func of the first NameSet'''
        self.n2.change_name_len_func(namemaker.estimate_syllables)
        self.assertWarns(namemaker.NameLenWarning, lambda: self.n1 & self.n2)
        result_set = self.n1 & self.n2
        self.assertIs(result_set._name_len_func, self.n1._name_len_func)

        # do the same test for iand
        self.assertWarns(namemaker.NameLenWarning, sneaky_iand, self.n1, self.n2)  # make sure a warning happens when intersecting n2 from n1 with a different name_len_func
        self.assertIs(namemaker.DEFAULT_NAME_LEN_FUNC, self.n1._name_len_func)      # make sure n1's name_len_func wasn't changed

    def test_and_string_error(self):
        ''' make sure an exception is raised when trying to intersect a string with a NameSet'''
        self.assertRaises(TypeError, lambda: self.n1 & 'hi')
        self.assertRaises(TypeError, sneaky_iand, self.n1, 'hi')


    ## Insertion and deletion tests

    def test_append(self):
        ''' makes sure a name can be appended to the NameSet correctly'''
        expected_set = namemaker.NameSet(test_names_1 + ['name 1'], order = self.n1._order)
        self.n1.append('name 1')
        self.assertEqual(self.n1._names, test_names_1 + ['name 1'])
        self.assertEqual(self.n1._avg_name_len, avg_len(self.n1, self.n1._name_len_func)) # make sure _avg_name_len is updated correctly
        self.assertEqual(set(self.n1._names), self.n1._names_set)                   # make sure the _names_set was updated correctly
        self.assertEqual(self.n1._markov_dict, expected_set._markov_dict)           # make sure the markov_dict updated correctly

    def test_add(self):
        ''' makes sure a name can be added to the NameSet correctly, only if it is not already in it'''
        copy_set = self.n1.copy()
        self.n1.add('name 1')    # this name is already in the NameSet, so adding it should change nothing
        self.assertTrue(copy_set == self.n1)

        expected_set = namemaker.NameSet(test_names_1 + ['name 100'], order = self.n1._order)
        self.n1.add('name 100')  # this name is not in the NameSet yet, so adding it should change the NameSet
        self.assertEqual(self.n1._names, test_names_1 + ['name 100'])
        self.assertEqual(self.n1._avg_name_len, avg_len(self.n1, self.n1._name_len_func)) # make sure _avg_name_len is updated correctly
        self.assertEqual(set(self.n1._names), self.n1._names_set)                   # make sure the _names_set was updated correctly
        self.assertEqual(self.n1._markov_dict, expected_set._markov_dict)           # make sure the markov_dict updated correctly

    def test_remove(self):
        ''' makes sure a name can be removed from the NameSet'''
        expected_set = namemaker.NameSet(test_names_1[1:], order = self.n1._order)
        self.n1.remove('name 1')
        self.assertEqual(self.n1._names, test_names_1[1:])                          # make sure the NameSet's names are equivalent to test_names_1 without the first name in it
        self.assertEqual(self.n1._avg_name_len, avg_len(self.n1, self.n1._name_len_func)) # make sure _avg_name_len is updated correctly
        self.assertEqual(set(self.n1._names), self.n1._names_set)                   # make sure the _names_set was updated correctly
        self.assertEqual(self.n1._markov_dict, expected_set._markov_dict)           # make sure the markov_dict updated correctly

        self.assertRaises(ValueError, self.n1.remove, 'name 1')                     # make sure an error is raised when trying to remove a name not in the NameSet

    def test_remove_duplicates(self):
        expected_set = namemaker.NameSet(['name1', 'name2', 'change the avg len'], order = self.n1._order)
        self.n3.append('change the avg len')
        self.n3.remove_duplicates()
        self.assertCountEqual(self.n3._names, set(test_names_3 + ['change the avg len']))
        self.assertEqual(self.n3._names_set, set(test_names_3 + ['change the avg len']))
        self.assertEqual(self.n3._avg_name_len, avg_len(self.n3, self.n3._name_len_func))   # make sure the average length was updated correctly
        self.assertEqual(self.n3._markov_dict, expected_set._markov_dict)           # make sure the markov_dict updated correctly


    # other manipulation tests
    def test_change_order(self):
        n = namemaker.NameSet(['name 1', 'name2'], order = 3)
        n.change_order(2)
        expected_dict = {'': ['n', 'n'],
                         'n': ['a', 'a'],
                         'na': ['m', 'm'],
                         'am': ['e', 'e'],
                         'me': [' ', '2'],
                         'e ': ['1'],
                         ' 1': [namemaker._END],
                         'e2': [namemaker._END]}
        self.assertEqual(n._markov_dict, expected_dict)
        self.assertEqual(n._order, 2)
        
        self.assertRaises(ValueError, n.change_order, 1.5)
        self.assertRaises(ValueError, n.change_order, -1)
        n.change_order(0)   # setting the order to 0 should work just fine

    def test_get_order(self):
        self.assertEqual(self.n1.get_order(), self.n1._order)

    def test_change_name_len_func(self):
        new_name_len_func = lambda name: 2
        self.n1.change_name_len_func(new_name_len_func)
        self.assertIs(self.n1._name_len_func, new_name_len_func)
        self.assertEqual(self.n1._avg_name_len, 2)

    def test_get_name_len_func(self):
        result = self.n1.get_name_len_func()
        self.assertIs(result, self.n1._name_len_func)

    def test_get_avg_name_len(self):
        result = self.n1.get_avg_name_len()
        self.assertEqual(self.n1._avg_name_len, result)

    def test_add_to_history(self):
        self.assertEqual(self.n1._history, set(test_names_1))
        self.n1.add_to_history('hey')
        self.n1.add_to_history(['hi', 'say', 'it', 'loud'])
        self.assertEqual(self.n1._history, set(test_names_1 + ['hey', 'hi', 'say', 'it', 'loud']))

    def test_get_history(self):
        result = self.n1.get_history()
        self.assertEqual(result, self.n1._history)
        self.assertIsNot(result, self.n1._history)

    def test_clear_history(self):
        self.n1.clear_history()
        self.assertEqual(self.n1._history, set())

    def test_link_histories(self):
        self.n1.link_histories(self.n2, self.n3)
        self.assertIs(self.n1._history, self.n2._history)
        self.assertIs(self.n1._history, self.n3._history)
        self.assertEqual(self.n1._history, set(test_names_1 + test_names_2 + test_names_3))

        self.n1.link_histories(self.n4)
        self.assertIs(self.n1._history, self.n4._history)                                       # linked to new NameSet
        self.assertIsNot(self.n1._history, self.n2._history)                                    # no longer linked to original group
        self.assertEqual(self.n1._history, set(test_names_1 + test_names_2 + test_names_3 + test_names_4))  # kept the original group's history plus this new NameSet's history
        self.assertIs(self.n2._history, self.n3._history)                                       # didn't unlink the other members of the original group
        self.assertEqual(self.n2._history, set(test_names_1 + test_names_2 + test_names_3))     # didn't change the original group's history

        self.n1.add_to_history('hi')
        self.assertIn('hi', self.n4._history)                                                   # make sure adding to the history of one adds to all
        self.n1.clear_history()
        self.assertEqual(self.n4._history, set())                                               # make sure clearing one clears all

    def test_unlink_history(self):
        self.n1.link_histories(self.n2, self.n3)
        self.n1.unlink_history()
        self.assertIsNot(self.n1._history, self.n2._history)                                    # make sure it's not linked to the original group any more
        self.assertIs(self.n2._history, self.n3._history)                                       # didn't unlink the other members of the original group
        self.assertEqual(self.n2._history, set(test_names_1 + test_names_2 + test_names_3))     # didn't change the original group's history
        self.assertEqual(self.n2._history, set(test_names_1 + test_names_2 + test_names_3))     # didn't change its own history

    def test_linked_history_copy(self):
        self.n1.link_histories(self.n2)
        copy_set = self.n1.copy()
        self.assertIs(self.n1._history, self.n2._history)
        self.assertIsNot(copy_set._history, self.n2._history)
        self.assertEqual(self.n1._history, copy_set._history)

class LoadingDataTests(unittest.TestCase):
    def test_make_name_set(self):
        names = ['name1', '', ' name2-', '$']
        cleaned_names = ['name1', 'name2']

        result = namemaker.make_name_set(names)
        expected_result = namemaker.NameSet(cleaned_names)
        self.assertTrue(result == expected_result)

        result = namemaker.make_name_set(names, clean_up = False)
        expected_result = namemaker.NameSet(names)
        self.assertTrue(result == expected_result)

        result = namemaker.make_name_set(names, order = 2)
        expected_result = namemaker.NameSet(cleaned_names, order = 2)
        self.assertTrue(result == expected_result)

        result = namemaker.make_name_set(names, name_len_func = namemaker.estimate_syllables)
        expected_result = namemaker.NameSet(cleaned_names, name_len_func = namemaker.estimate_syllables)
        self.assertTrue(result == expected_result)

        result = namemaker.make_name_set('male first names', clean_up = False)
        male_names = namemaker.get_names_from_file('male first names')
        expected_result = namemaker.NameSet(male_names)
        self.assertTrue(result == expected_result)

    def test_get_names_from_file(self):
        names = namemaker.get_names_from_file('male first names')
        self.assertIn('John', names)
        self.assertEqual(len(names), 1000)

        names = namemaker.get_names_from_file('male first names.txt')
        self.assertIn('John', names)
        self.assertEqual(len(names), 1000)

    def test_clean(self):
        names = ['name1', '', ' name2-', '$']
        cleaned_names = ['name1', 'name2']
        result = namemaker.clean(names)
        self.assertEqual(result, cleaned_names)
        self.assertIsNot(result, names)

    def test_clean_blanks(self):
        names = ['name1', '', ' name2-', '$']
        cleaned_names = ['name1', ' name2-']
        result = namemaker.clean_blanks(names)
        self.assertEqual(result, cleaned_names)
        self.assertIsNot(result, names)

        result = namemaker.clean_blanks(names, blank_names = ['name1'])
        self.assertEqual(result, [' name2-'])

    def test_clean_extra_symbols(self):
        names = ['name1', '', ' name2-', '$']
        cleaned_names = ['name1', '', 'name2', '']
        result = namemaker.clean_extra_symbols(names)
        self.assertEqual(result, cleaned_names)
        self.assertIsNot(result, names)

class BannedWordTests(unittest.TestCase):
    ''' Tests setting and adding banned words.
        Making sure banned words aren't allowed in names is handled in CoreFunctionalityTests'''
    def cleanUp(self):
        namemaker.banned_words = set()

    def test_set_banned_words(self):
        namemaker.set_banned_words(['hey', 'hi'])
        self.assertEqual(namemaker.banned_words, {'hey', 'hi'})

        namemaker.set_banned_words(['hello'])
        self.assertEqual(namemaker.banned_words, {'hello'})

        self.assertRaises(TypeError, namemaker.set_banned_words, 'hi')

    def test_add_banned_words(self):
        namemaker.add_banned_words(['hey', 'hi'])
        self.assertEqual(namemaker.banned_words, {'hey', 'hi'})

        namemaker.add_banned_words(['hello'])
        self.assertEqual(namemaker.banned_words, {'hey', 'hi', 'hello'})

        self.assertRaises(TypeError, namemaker.add_banned_words, 'hi')

    def test_get_banned_words(self):
        namemaker.set_banned_words(['hey', 'hi'])
        result = namemaker.get_banned_words()
        self.assertEqual(result, {'hey', 'hi'})
        self.assertIsNot(result, namemaker.banned_words)

class RNGTests(unittest.TestCase):
    def setUp(self):
        self.rng = namemaker.rng

    def cleanUp(self):
        namemaker.rng = self.rng

    def test_get_rng(self):
        rng = namemaker.get_rng()
        self.assertIs(self.rng, rng)

    def test_set_rng(self):
        new_rng = random.Random()
        namemaker.set_rng(new_rng)
        self.assertIs(new_rng, namemaker.rng)

class MiscTests(unittest.TestCase):
    def test_sample(self):
        pass    ## TODO: figure out how to test printed output

    def test_stress_test(self):
        pass    ## TODO: figure out how to test printed output

    def test_estimate_syllables(self):
        result_1 = namemaker.estimate_syllables('avacado')
        result_2 = namemaker.estimate_syllables('avacados')
        self.assertEqual(result_1, result_2)
        self.assertTrue(3 <= result_1 <= 5)     # don't be off by more than 1 syllable with a 4 syllable word (+/- 25%)

        result = namemaker.estimate_syllables('antidisestablishmentarianism')
        self.assertTrue(9 <= result <= 15)      # don't be off by more than 3 syllable with a 12 syllable word (+/- 25%)

        self.assertEqual(namemaker.estimate_syllables(''), 0)

        # add the proper number of syllables for each number
        self.assertEqual(namemaker.estimate_syllables('0'), 2)
        self.assertEqual(namemaker.estimate_syllables('1'), 1)
        self.assertEqual(namemaker.estimate_syllables('2'), 1)
        self.assertEqual(namemaker.estimate_syllables('3'), 1)
        self.assertEqual(namemaker.estimate_syllables('4'), 1)
        self.assertEqual(namemaker.estimate_syllables('5'), 1)
        self.assertEqual(namemaker.estimate_syllables('6'), 1)
        self.assertEqual(namemaker.estimate_syllables('7'), 2)
        self.assertEqual(namemaker.estimate_syllables('8'), 1)
        self.assertEqual(namemaker.estimate_syllables('9'), 1)

        # make sure hyphens and spaces work correctly
        result_1 = namemaker.estimate_syllables('testit')
        result_2 = namemaker.estimate_syllables('test-it')
        result_3 = namemaker.estimate_syllables('test it')
        self.assertEqual(result_1, result_2)
        self.assertEqual(result_1, result_3)
        self.assertEqual(result_1, 2)




if __name__ == '__main__':
    unittest.main()






