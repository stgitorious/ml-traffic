from sklearn.cross_validation import KFold
from sklearn.decomposition import PCA
import itertools
import random

# own packages
from image_loader import *



def split_kfold(images, k):
    kf = KFold(len(images), n_folds=k)
    return [([images[i] for i in trainIndices], [images[i] for i in testIndices]) for trainIndices, testIndices in kf]

def extract_pole_nr(image):
    _, tail = os.path.split(image.filename)
    return int(tail.split('_')[0])

def split_special(images):
    class_by_pole = list([list([list(image_by_pole)
                                for _, image_by_pole in itertools.groupby(sorted(img_by_class, key=lambda l: extract_pole_nr(l)), lambda y: extract_pole_nr(y))])
                          for cl, img_by_class in itertools.groupby(sorted(images, key=lambda p: p.label), lambda x: x.label)])
    max_allowed_folds = min([len(x) for x in class_by_pole])

    # Now we make sure that for each class, it is added to at least each fold
    # Warning: folds = [[]] * max_allowed_folds uses the same array reference for each!
    folds = []
    for fold in range(max_allowed_folds):
        folds.append([])

    for cl in class_by_pole:
        permutations = list(range(len(cl)))
        random.shuffle(permutations)

        # Spread permutation evenly over all folds
        while len(permutations) >= max_allowed_folds:
            for fold in range(max_allowed_folds):  # spread over the available folds
                image_group = cl[permutations.pop(0)]
                folds[fold].extend(image_group)

        # Now take care of the remaining items (distribute randomly, no other choice)
        for i in range(len(permutations)):
            fold = random.randrange(len(permutations))
            image_group = cl[permutations.pop(0)]
            folds[fold].extend(image_group)

    # Now that we generated the folds, we generate fold sets
    return [(list(itertools.chain(*[folds[k] for k in [j for j in range(max_allowed_folds) if j != i]])), folds[i]) for i in range(max_allowed_folds)]


def cross_validate(images, feature_combiner, trainer_function, k=1, use_super_class=True, number_of_pca_components=0, verbose=True):
    #fold = split_kfold(images, k)
    fold = split_special(images)
    print('Split into %d folds' % len(fold))

    error_ratios = []
    for i, (train_images, test_images) in enumerate(fold):
        assert len(train_images) + len(test_images) == len(images)
        if verbose:
            print('-------- calculating fold %d --------' % (i + 1))

        # Feature extraction
        feature_extraction(train_images, feature_combiner, verbose=verbose)
        feature_extraction(test_images, feature_combiner, verbose=verbose)
        # Train
        trainer = trainer_function()
        if verbose:
            print('Using ', type(trainer), ' for trainer.')
        train_data = [image.getFeatureVector() for image in train_images]
        pca = None
        if number_of_pca_components > 0:
            pca = PCA(n_components=min(number_of_pca_components, len(train_images[0].features)))
            pca.fit(train_data)
            train_data = pca.transform(train_data)
        train_classes = [image.super_label if use_super_class else image.label for image in train_images]
        trainer.train(train_data, train_classes)
        # Predict
        test_data = [image.getFeatureVector() for image in test_images]
        if pca:
            test_data = pca.transform(test_data)  # perform PCA
        predictions = trainer.predict(test_data)
        # Compare predictions with ground truths
        ground_truths = [image.super_label if use_super_class else image.label for image in test_images]
        errors = []
        for image, prediction, ground_truth in zip(test_images, predictions, ground_truths):
            if prediction != ground_truth:
                if verbose:
                    print('\r    [ERROR] for image %s I predicted "%s" but the sign actually was "%s"' % (
                    image.filename, prediction, ground_truth))
                errors.append([image, prediction, ground_truth])
        if verbose:
            sys.stdout.write('\r    test calculation [100 %]\n')
        error = float(len(errors)) / len(test_images)
        if verbose:
            print('    error ratio of fold: %f' % error)
        error_ratios.append(error)

    mean_result = np.mean(error_ratios)
    std_result = np.std(error_ratios)
    if verbose:
        print('-------- folds done --------\n')
        print('mean error_ratio is %f (std: %f)' % (mean_result, std_result))
    return mean_result