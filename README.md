# cAML


## Description
Analogical Modeling (Skousen, 1989) is an exemplar-based approach to predict
language behavior. Its predictions are based on a dataset of occurrences
(lexicon).

This is a Python implementation of the algorithm extended by an optional
numerical parameter to modify each exemplar's weight.

This README contains a brief overview on how to run the algorithm.
The [Step-by-Step Guide](doc.md) gives more detailed instructions.

## Installation

After downloading the repository, you can install the project like this:

```bash
pip install --editable .
```

## 📚 Requirements

As the python code in this repository is written in python 3.12,
this or a more recent version is highly recommended. Compatibility with older
versions of python can't be guaranteed. Additionally, the code requires the
following packages:

- pandas
- matplotlib (for the evaluation output)
- scikit-learn (for the evaluation output)
- tqdm
- pandastable (GUI only)
- TkToolTip (GUI only)


You can install the requirements from `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Usage
Running `aml.py` will automatically create three output files:
1. `<output>_gangs.csv`: gang effects
2. `<output>_analogical_sets.csv`: analogical sets
3. `<output>_distributions.csv`: distributions

where `<output>` can be either a prefix (`my_data`) or a path to a directory followed by a prefix (`path/to/directory/my_data`)
```bash
python3 aml.py -l <data.csv> -o <output>
```

### Additional options:
- `-t` or `--test` `<test_file>` to use a separate document for testing (instead of predicting each instance in the lexicon)
- `-w` or `--weight_column` `column_name` specifies a column for weights
- `-th` or `--threshold` `value` will drop any instances with a weight below that threshold
- `--inclusive` to drop instances with a weight equal to the threshold (has no effect without threshold)
- `-mt` or `--max_threshold` `value` will drop any instances with a weight above that threshold
- `--max_inclusive` to drop instances with a weight equal to the threshold (has no effect without upper threshold)
- `-c` or `--class_column` to specify the class column by name (defaults to last column)
- `-d` or `--drop_duplicates`
    - any instance with the same features and the same class within the lexicon will be dropped
- `--ignore_columns` to specify a list of columns to ignore (using their names)
- `-L` or `--linear` to use linear instead of quadratic calculation of pointer values
- `-k` or `--keep_test` to keep test exemplars in the training set
    - if True, the instance to be predicted will not be removed from the lexicon (if used as test set) before prediction
    - if False (default), full matches (instances with the same features, but not necessarily the same class) are ignored
- `-i` or `--ignore_unknowns`
    - any attribute that includes unknown values will be ignored for all instances
- `-D` `--debug` to run the classifier in debug mode (generates more outputs)
- `-n` or `--non_specified_data` `<option>` where `<option>` is one out of {`match`, `mismatch`, `variable`} to
 determine the treatment of non-specified data (marked by `=`)
    - match: non-specified values match everything
    - mismatch: non-specified values don't match anything
    - variable: non-specified values are treated like a variable, thus only matching other non-specified values



## Alternative Versions
- [weka version](https://github.com/garfieldnate/Weka_AnalogicalModeling) (Java) by Nathan Glenn
- [TrAML](https://github.com/SabineArndtLappe/TrAML) (Perl)

## License
Released under the GNU General Public Licence v.3 (see the LICENSE file for details). Copyright Jasmin Wiese, 2025.


This project was funded by the **Deutsche Forschungsgemeinschaft** 
(DFG, German Research Foundation, grant no. 549185879).
