import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.utils import normalize
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tqdm import tqdm

IUPAC_CODES = {
    "A": 1.8,
    "C": 2.5,
    "D": -3.5,
    "E": -3.5,
    "F": 2.8,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "K": -3.9,
    "L": 3.8,
    "M": 1.9,
    "N": -3.5,
    "P": -1.6,
    "Q": -3.5,
    "R": -4.5,
    "S": -0.8,
    "T": -0.7,
    "V": 4.2,
    "W": -0.9,
    "Y": -1.3,
    "*": -0.48,
}

IUPAC_CODES_1 = {
    "A": 0.0373,
    "C": 0.0829,
    "D": 0.1263,
    "E": 0.0058,
    "F": 0.0946,
    "G": 0.0050,
    "H": 0.0242,
    "I": 0,
    "K": 0.0371,
    "L": 0,
    "M": 0.0823,
    "N": 0.0036,
    "P": 0.0198,
    "Q": 0.0761,
    "R": 0.0959,
    "S": 0.0829,
    "T": 0.0941,
    "V": 0.0057,
    "W": 0.0548,
    "Y": 0.0516,
    "*": 0,
}

IUPAC_CODES_2 = {
    "A": -1,
    "C": -2,
    "D": -3,
    "E": -4,
    "F": -5,
    "G": -6,
    "H": -7,
    "I": -8,
    "K": -9,
    "L": -10,
    "M": 1,
    "N": 2,
    "P": 3,
    "Q": 4,
    "R": 5,
    "S": 6,
    "T": 7,
    "V": 8,
    "W": 9,
    "Y": 10,
    "*": 0,
}


def aa2int(i):
    try:
        return  IUPAC_CODES[i]
    except Exception as e:
        return  IUPAC_CODES["*"]


def obtain_dataset_wordvectors(
    dataset_file="", labels_file="", sequence_file="", maxlen=1500
):
    dataset = []
    sequences = []

    lengths = []
    for ix, i in tqdm(enumerate(open(dataset_file))):
        i = i.split()
        item = np.array([float(k) for k in i])
        dataset.append(item)
        lengths.append(len(item))

    for i in tqdm(open(sequence_file)):
        item = [[aa2int(k)] for k in i]
        sequences.append(item)

    sequences = pad_sequences(
        sequences, maxlen=maxlen, padding="post", dtype="float32", truncating="post"
    )

    dataset = np.array(dataset)
    sequences = np.array(sequences)

    print(dataset.shape, sequences.shape, set(lengths))

    return normalize(dataset, axis=-1, order=2), sequences


def obtain_dataset_alignments(dataset_file="", features_file="", file_order=""):
    """ From an alignment file generate a matrix of values,
        the order of the matrix features depends on the
        features_file, it has to be the same all the time

        file order: contains a list with the entries in the order
                    that they are used for the other sets. For instance,
                    the gene_1 in the fasta file, has to be the same 1
                    position in this file.
        features file: this file contains the list of genes that were
                    used as features, also known as the centroids.
    """

    dataset = {}
    features = {i.strip().split()[0]: ix for ix, i in enumerate(open(features_file))}

    for i in open(dataset_file):
        i = i.split()
        try:
            assert dataset[i[0]]
        except Exception as e:
            dataset[i[0]] = np.zeros(len(features))
        #
        dataset[i[0]][features[i[1]]] = float(i[-1])

    samples_oder = [i.strip().split("\t")[0] for i in open(file_order)]

    ordered_dataset = []
    for i in samples_oder:
        try:
            ordered_dataset.append(dataset[i])
        except Exception as e:
            ordered_dataset.append(np.zeros(len(features)))
    scaler = MinMaxScaler()

    return [scaler.fit_transform(np.array(ordered_dataset)), features]


def obtain_test_labels(classes={}, groups={}, labels_file=""):
    """[
        This script subtract the test labes by using the keywords
        (classes/groups) from the training.
    ]

    Keyword Arguments:
        classes {[list]} -- [object with classes names] (default: {[]})
        groups {[list]} -- [object with group names] (default: {[]})
        labels_file {str} -- [file with information] (default: {''})
    """

    total_categories = len(classes)
    total_groups = len(groups)
    group_labels = []
    category_labels = []

    for i in open(labels_file):
        i = i.strip().split("\t")
        #
        arg_id, arg_classes, arg_name, arg_group = i[0].split("|")
        #
        category_label = np.zeros(total_categories)
        group_label = np.zeros(total_groups)
        for arg_class in arg_classes.split(":"):
            category_label[classes[arg_class]] = 1
        #
        group_label[groups[arg_group]] = 1
        group_labels.append(group_label)
        category_labels.append(category_label)

    return np.array(group_labels), np.array(category_labels)


def obtain_labels(labels_file="", test_labes_file=""):
    """

    From the generated header files, subtract the labels for each ARG.
    Focus on groups and antibiotic categories

    """
    categories = {}
    groups = {}
    category_index = 0
    group_index = 0
    index_start = []

    # let's traverse both training and testing, in the case when the
    # testing has labels that are not considered in the training we still
    # need to add those to the labels
    for _file in [labels_file, test_labes_file]:
        for i in open(_file):
            i = i.strip().split("\t")
            index_start.append(int(i[1]))
            arg_id, arg_classes, arg_name, arg_group = i[0].split("|")
            for arg_class in arg_classes.split(":"):
                try:
                    assert categories[arg_class]
                except Exception as e:
                    categories[arg_class] = category_index
                    category_index += 1
            try:
                assert groups[arg_group]
            except Exception as e:
                groups[arg_group] = group_index
                group_index += 1

    total_categories = len(categories)
    total_groups = len(groups)
    group_labels = []
    category_labels = []

    categories = {i: ix for ix, i in enumerate(categories)}
    groups = {i: ix for ix, i in enumerate(groups)}

    for i in open(labels_file):
        i = i.strip().split("\t")
        #
        arg_id, arg_classes, arg_name, arg_group = i[0].split("|")
        #
        category_label = np.zeros(total_categories)
        group_label = np.zeros(total_groups)
        for arg_class in arg_classes.split(":"):
            category_label[categories[arg_class]] = 1
        #
        group_label[groups[arg_group]] = 1
        group_labels.append(group_label)
        category_labels.append(category_label)

    return [
        categories,
        groups,
        index_start,
        np.array(group_labels),
        np.array(category_labels),
    ]

