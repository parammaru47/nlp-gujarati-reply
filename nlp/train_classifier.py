import sys
import numpy as np
import pandas as pd
import joblib
from gensim.models import FastText
from gensim.utils import simple_preprocess
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report

class MeanFastTextTransformer(BaseEstimator, TransformerMixin):
    """
    Extracts dense semantic vectors from the Gensim FastText model.
    Averages the word vectors for each incoming sentence.
    """
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None

    def fit(self, X, y=None):
        if self.model is None:
            print("Loading FastText model into memory...")
            self.model = FastText.load(self.model_path)
        return self

    def transform(self, X):
        if self.model is None:
            self.model = FastText.load(self.model_path)
            
        vector_size = self.model.vector_size
        X_transformed = np.zeros((len(X), vector_size))
        
        for i, text in enumerate(X):
            tokens = simple_preprocess(text)
            valid_tokens = [word for word in tokens if word in self.model.wv.key_to_index]
            
            if valid_tokens:
                # Mean pooling of all known word vectors in the sentence
                X_transformed[i] = np.mean([self.model.wv[word] for word in valid_tokens], axis=0)
            else:
                # Fallback zero vector for completely Out-Of-Vocabulary sentences
                X_transformed[i] = np.zeros(vector_size)
                
        return X_transformed

def train_dense_dialogue_act_model():
    dataset_path = "data/dialogue_acts.csv"
    ft_model_path = "data/gu_fasttext_lite.model"
    classifier_output_path = "data/dialogue_act_model_dense.joblib"

    try:
        df = pd.read_csv(dataset_path)
    except FileNotFoundError:
        sys.stderr.write(f"FATAL: Could not locate {dataset_path}\n")
        sys.exit(1)

    X = df["message"].fillna("")
    y = df["dialogue_act"]

    # Semantic FastText Features (Module 1.5)
    fasttext_features = MeanFastTextTransformer(model_path=ft_model_path)
    
    # Morphological Subword Features (Module 1.2 & 1.4)
    char_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1, sublinear_tf=True)

    # Combine Dense and Sparse representations
    features = FeatureUnion([
        ("semantic_dense", fasttext_features),
        ("morphology_sparse", char_vectorizer)
    ], transformer_weights={"semantic_dense": 0.2, "morphology_sparse": 1.0})

    classifier = CalibratedClassifierCV(LinearSVC(C=5.0, class_weight="balanced", max_iter=3000, random_state=42))

    pipeline = Pipeline([
        ("features", features),
        ("classifier", classifier)
    ])

    print("Fitting integrated FeatureUnion pipeline...")
    pipeline.fit(X, y)
    
    preds = pipeline.predict(X)
    print("\nIntegrated Dense Classification Report:")
    print(classification_report(y, preds, zero_division=0))

    joblib.dump(pipeline, classifier_output_path)
    print(f"\nPipeline successfully saved to {classifier_output_path}")

if __name__ == "__main__":
    train_dense_dialogue_act_model()
