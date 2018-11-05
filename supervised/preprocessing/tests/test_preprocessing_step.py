import json
import copy
import unittest
import tempfile
import numpy as np
import pandas as pd
import uuid

from preprocessing_missing import PreprocessingMissingValues
from preprocessing_categorical import PreprocessingCategorical
from preprocessing_step import PreprocessingStep
from utils.constants import PROJECT_BIN_CLASS, PROJECT_REGRESSION

class PreprocessingStepTest(unittest.TestCase):

    def test_constructor_preprocessing_step(self):
        ps = PreprocessingStep(missing_values_method = None, categorical_method = None, scale_method = None)
        self.assertTrue(ps._missing_values is None)
        self.assertTrue(ps._categorical is None)
        self.assertTrue(ps._categorical_y is None)

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, categorical_method = None, scale_method = None)
        self.assertTrue(ps._missing_values is not None)
        self.assertTrue(ps._categorical is None)
        self.assertTrue(ps._categorical_y is None)

        ps = PreprocessingStep(missing_values_method = None, categorical_method = PreprocessingCategorical.CONVERT_INTEGER, scale_method = None)
        self.assertTrue(ps._missing_values is None)
        self.assertTrue(ps._categorical is not None)
        self.assertTrue(ps._categorical_y is None)


    def test_exclude_missing_targets_all_good(self):
        # training data
        d = {'col1': [1, 1, 1, 3],
             'col2': [5, 6, 7, 0],
             'col3': [1, 1, 1, 3],
             'col4': [2, 2, 4, 3],
             'y':    [0, 1, 0, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep()
        X_train, y_train = ps._exclude_missing_targets(X_train, y_train)

        self.assertEqual(4, X_train.shape[0])
        self.assertEqual(4, y_train.shape[0])


    def test_exclude_missing_targets(self):
        # training data
        d = {'col1': [1, 1, 1, 3],
             'col2': [5, 6, 7, 0],
             'col3': [1, 1, 1, 3],
             'col4': [2, 2, 4, 3],
             'y':    [0, np.nan, 0, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep()
        X_train, y_train = ps._exclude_missing_targets(X_train, y_train)

        self.assertEqual(3, X_train.shape[0])
        self.assertEqual(3, y_train.shape[0])


    def test_run_exclude_missing_targets(self):
        # training data
        d = {'col1': [1, 1, 1, 3],
             'col2': [5, 6, 7, 0],
             'col3': [1, 1, 1, 3],
             'col4': [2, 2, 4, 3],
             'y':    [0, np.nan, 0, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep()
        X_train, y_train, _, _ = ps.run(X_train = X_train, y_train = y_train)

        self.assertEqual(3, X_train.shape[0])
        self.assertEqual(3, y_train.shape[0])

    def test_run_all_good(self):
        # training data
        d = {'col1': [1, 1, 1, 3],
             'col2': [5, 6, 7, 0],
             'col3': [1, 1, 1, 3],
             'col4': [2, 2, 4, 3],
             'y':    [0, 1, 0, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_INTEGER)
        X_train, y_train, _, _ = ps.run(X_train = X_train, y_train = y_train)

        for col in ['col1', 'col2', 'col3', 'col4']:
            self.assertTrue(col in X_train.columns)

        params_json = ps.to_json()
        self.assertFalse(params_json) # should be empty

    def test_run_fill_median_convert_integer(self):
        # training data
        d = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [0, 1, 0, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_INTEGER)
        X_train, y_train, _, _ = ps.run(X_train = X_train, y_train = y_train)

        for col in ['col1', 'col2', 'col3', 'col4']:
            self.assertTrue(col in X_train.columns)
        self.assertEqual(X_train['col1'][2], 1)
        self.assertEqual(X_train['col2'][2], 0)
        self.assertEqual(X_train['col4'][0], 0)
        self.assertEqual(X_train['col4'][1], 0)
        self.assertEqual(X_train['col4'][2], 1)
        self.assertEqual(X_train['col4'][3], 2)

        params_json = ps.to_json()
        self.assertTrue('missing_values' in params_json)
        self.assertTrue('categorical' in params_json)
        self.assertTrue('categorical_y' not in params_json)

        self.assertTrue('fill_params' in params_json['missing_values'])
        self.assertEqual('na_fill_median', params_json['missing_values']['fill_method'])
        self.assertTrue('convert_params' in params_json['categorical'])
        self.assertEqual('categorical_to_int', params_json['categorical']['convert_method'])

    def test_run_fill_median_convert_integer_validation_dataset(self):
        # training data
        d = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [0, 1, 1, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        d_test = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [np.nan, 1, np.nan, 1]}
        df_test = pd.DataFrame(data=d_test)
        X_test = df_test.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_test = df_test.loc[:, 'y']

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_INTEGER)
        X_train, y_train, X_test, y_test = ps.run(X_train = X_train, y_train = y_train, \
                                                    X_test = X_test, y_test = y_test)

        for col in ['col1', 'col2', 'col3', 'col4']:
            self.assertTrue(col in X_train.columns)
            self.assertTrue(col in X_test.columns)

        self.assertEqual(4, X_train.shape[0])
        self.assertEqual(4, y_train.shape[0])
        self.assertEqual(2, X_test.shape[0])
        self.assertEqual(2, y_test.shape[0])


    def test_run_on_y_only(self):
        d = {'y': ['a', 'b', 'a', 'b']}
        df = pd.DataFrame(data=d)
        y_train = df.loc[:, 'y']
        ps = PreprocessingStep()
        _, y_train, _, _ = ps.run(y_train = y_train)
        self.assertEqual(4, y_train.shape[0])
        self.assertEqual(0, y_train[0])
        self.assertEqual(1, y_train[1])


    def test_run_on_y_only_validation(self):
        d = {'y': ['a', 'b', 'a', 'b']}
        df = pd.DataFrame(data=d)
        y_train = df.loc[:, 'y']

        d_test = {'y':    [np.nan, 'a', np.nan, 'b']}
        df_test = pd.DataFrame(data=d_test)
        y_test = df_test.loc[:, 'y']

        ps = PreprocessingStep()
        _, y_train, _, y_test = ps.run(y_train = y_train, y_test = y_test)

        self.assertEqual(4, y_train.shape[0])
        self.assertEqual(2, y_test.shape[0])
        self.assertEqual(0, y_train[0])
        self.assertEqual(1, y_train[1])
        self.assertEqual(0, y_test[0])
        self.assertEqual(1, y_test[1])

    def test_to_and_from_json_run_fill_median_convert_integer(self):
        # training data
        d = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [0, 1, 0, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_INTEGER)
        X_train, y_train, _, _ = ps.run(X_train = X_train, y_train = y_train)

        ps2 = PreprocessingStep()
        ps2.from_json(ps.to_json())
        del ps

        d_test = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [np.nan, np.nan, 1, 1]}
        df_test = pd.DataFrame(data=d_test)
        X_test = df_test.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_test = df_test.loc[:, 'y']

        _, _, X_test, y_test = ps2.run(X_test = X_test, y_test = y_test)

        self.assertEqual(2, y_test.shape[0])
        self.assertEqual(2, np.sum(y_test))
        self.assertEqual(1, X_test['col1'][0])
        self.assertEqual(0, X_test['col2'][0])


    def test_run_fill_median_convert_one_hot_validation_dataset(self):
        # training data
        d = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [0, 1, 1, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        d_test = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'z', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [np.nan, 1, np.nan, 1]}
        df_test = pd.DataFrame(data=d_test)
        X_test = df_test.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_test = df_test.loc[:, 'y']

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_ONE_HOT)
        X_train, y_train, X_test, y_test = ps.run(X_train = X_train, y_train = y_train, \
                                                    X_test = X_test, y_test = y_test)

        for col in ['col1', 'col2_a', 'col3', 'col4_a', 'col4_b', 'col4_c']:
            self.assertTrue(col in X_train.columns)
            self.assertTrue(col in X_test.columns)

        self.assertEqual(4, X_train.shape[0])
        self.assertEqual(2, X_test.shape[0])
        self.assertEqual(4, np.sum(X_train['col2_a']))
        self.assertEqual(2, np.sum(X_train['col4_a']))
        self.assertEqual(1, np.sum(X_train['col4_b']))
        self.assertEqual(1, np.sum(X_train['col4_c']))
        self.assertEqual(0, X_test.loc[0, 'col2_a'])
        self.assertEqual(1, X_test.loc[1, 'col2_a'])


    def test_run_fill_median_convert_one_hot_big_categorical(self):

        a_lot = 250
        cs = []
        for i in xrange(a_lot):
            cs.append(str(uuid.uuid4().get_hex().upper()[0:6]))

        d = {'col1': cs,
             'col2': ['a', 'b'] * (a_lot / 2),
             'col3': range(a_lot),
             'col4': range(a_lot)}

        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        X_train_2 = copy.deepcopy(X_train)

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_ONE_HOT)
        X_train, _, _, _ = ps.run(X_train = X_train)

        for col in ['col1', 'col2_b', 'col3', 'col4']:
            self.assertTrue(col in X_train.columns)

        self.assertTrue(np.max(X_train['col1']) > 0.90*a_lot) # there can be duplicates ;)
        self.assertEqual(np.max(X_train['col2_b']), 1)
        self.assertEqual(np.sum(X_train['col2_b']), a_lot / 2)


        ps2 = PreprocessingStep()
        ps2.from_json(ps.to_json())
        del ps
        # apply preprocessing loaded from json
        _, _, X_train_2, _ = ps2.run(X_test = X_train_2)
        for col in ['col1', 'col2_b', 'col3', 'col4']:
            self.assertTrue(col in X_train_2.columns)

        self.assertTrue(np.max(X_train_2['col1']) > 0.90*a_lot) # there can be duplicates ;)
        self.assertEqual(np.max(X_train_2['col2_b']), 1)
        self.assertEqual(np.sum(X_train_2['col2_b']), a_lot / 2)

    def test_convert_target(self):
        d = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [2, 2, 1, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_ONE_HOT,
                                project_task = PROJECT_BIN_CLASS)
        X_train, y_train, _, _ = ps.run(X_train = X_train, y_train = y_train)

        self.assertEqual(2, len(np.unique(y_train)))
        self.assertTrue(0 in np.unique(y_train))
        self.assertTrue(1 in np.unique(y_train))

    def test_dont_convert_target(self):
        d = {'col1': [1, 1, np.nan, 3],
             'col2': ['a', 'a', np.nan, 'a'],
             'col3': [1, 1, 1, 3],
             'col4': ['a', 'a', 'b', 'c'],
             'y':    [2, 2, 1, 1]}
        df = pd.DataFrame(data=d)
        X_train = df.loc[:, ['col1', 'col2', 'col3', 'col4']]
        y_train = df.loc[:, 'y']

        ps = PreprocessingStep(missing_values_method = PreprocessingMissingValues.FILL_NA_MEDIAN, \
                                categorical_method = PreprocessingCategorical.CONVERT_ONE_HOT,
                                project_task = PROJECT_REGRESSION)
        X_train, y_train, _, _ = ps.run(X_train = X_train, y_train = y_train)

        self.assertEqual(2, len(np.unique(y_train)))
        self.assertTrue(1 in np.unique(y_train))
        self.assertTrue(2 in np.unique(y_train))


if __name__ == '__main__':
    unittest.main()