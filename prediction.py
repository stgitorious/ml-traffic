from os.path import basename
from image_loader import *

def train_and_predict(trainer_function, feature_combiner, train_directories=['data/train'],
                      test_directories=['data/test'], augment=True):
    # Load data
    trainer = trainer_function()
    train_images = load(train_directories, True)
    if len(train_images) == 0:
        print('Could not find train images. Aborting')
        return

    test_images = load(test_directories, False, False)
    if len(test_images) == 0:
        print('Could not find test images. Aborting')
        return

    if augment:
        train_images = augment_images(train_images)
        print('Augmented train images.')

    print('Images loaded')

    # Feature extraction
    feature_extraction(train_images, feature_combiner)
    feature_extraction(test_images, feature_combiner)
    print('Features extracted')

    # Free images
    for img in train_images:
        img.dispose_image()

    for img in test_images:
        img.dispose_image()
    print('Freed image memory')

    # Feature transform
    train_data = [image.get_feature_vector() for image in train_images]
    # Train model
    train_classes = [image.label for image in train_images]
    trainer.train(train_data, train_classes)
    print('Training complete!!')

    # Predict class of test images
    file = open('result.csv', 'w')
    file.write('Id,%s\n' % str.join(',', trainer.classes))
    for image in test_images:
        test_data = image.get_feature_vector()
        predictions = trainer.predict_proba(test_data)
        identifier = int(os.path.splitext(basename(image.filename))[0])
        file.write('%d,%s\n' % (identifier, str.join(',', [('%.13f' % p) for p in predictions[0]])))
    file.close()