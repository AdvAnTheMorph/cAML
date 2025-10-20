# AnalogicalModelingPython


## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

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

You can install the requirements from `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Usage
Running `aml.py` will automatically create three output files:
1. `<output>_gangs.csv`: gang effects
2. `<output>_analogical_sets.csv`: analogical sets
3. `<output>_distributions.csv`: distributions
```bash
python3 aml.py -l <data.csv> -o <output>
```
### Additional options:
- `-t` or `--test` `<test_file>` to use a separate document for testing (instead of predicting each instance in the lexicon)
- `-d` or `--drop_duplicates` to drop duplicated instances
- `--ignore_columns` to specify a list of column indices to ignore (starting with 0!)
- `-L` or `--linear` to use linear instead of quadratic calculation of pointer values
- `-K` or `--keep_test` to keep test exemplars in the training set
- `-I` or `--ignore_unknowns` to ignore attributes with unknown values
- `-D` `--debug` to run the classifier in debug mode (generates more outputs)
- `-M` or `--missing_data` `<option>` where `<option>` is one out of {`match`, `mismatch`, `variable`} to determine the treatment of missing data
