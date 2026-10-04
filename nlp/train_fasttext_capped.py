import os
import sys
from itertools import islice
from gensim.models import FastText
from gensim.utils import simple_preprocess

class GujaratiCorpusStreamer:
    """Streams exactly 2 million lines from the disk, then stops."""
    def __init__(self, file_path, limit=2000000):
        self.file_path = file_path
        self.limit = limit

    def __iter__(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            # islice stops reading the file once the limit is hit
            for line in islice(file, self.limit):
                yield simple_preprocess(line)

def train_fasttext_capped():
    corpus_path = "data/gu.txt"
    model_path = "data/gu_fasttext_lite.model"
    
    if not os.path.exists(corpus_path):
        sys.stderr.write(f"FATAL: Corpus not found at {corpus_path}\n")
        sys.exit(1)

    print("Initializing capped FastText training (8M lines)...")
    sentences = GujaratiCorpusStreamer(corpus_path, limit=8000000)
    
    model = FastText(vector_size=100, window=5, min_count=3, workers=4, sg=0, epochs=2)
    
    print("Building vocabulary stream...")
    model.build_vocab(corpus_iterable=sentences)
    
    print("Training dense vectors (This should take under 5 minutes)...")
    model.train(corpus_iterable=sentences, total_examples=model.corpus_count, epochs=model.epochs)
    
    model.save(model_path)
    print("Lite Semantic space compiled successfully.")

if __name__ == "__main__":
    train_fasttext_capped()
