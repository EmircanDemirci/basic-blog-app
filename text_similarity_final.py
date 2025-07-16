from collections import Counter
import math
import re

class TextSimilarity:
    def __init__(self, doc1, doc2):
        self.doc1 = doc1
        self.doc2 = doc2

        self.tokens1 = self.tokenize(self.doc1)
        self.tokens2 = self.tokenize(self.doc2)

        self.vocab = sorted(set(self.tokens1 + self.tokens2))

    def tokenize(self, text):
        if isinstance(text, list):
            text = " ".join(text)
        return re.findall(r'\b\w+\b', text.lower())

    def compute_tf(self, tokens):
        """Term Frequency hesapla"""
        if not tokens:
            return [0] * len(self.vocab)

        counts = Counter(tokens)
        return [counts[word] / len(tokens) for word in self.vocab]

    def compute_idf_standard(self):
        """Standart IDF (2 doküman için problemli)"""
        N = 2
        idf_values = []
        for word in self.vocab:
            df = sum(1 for tokens in [self.tokens1, self.tokens2] if word in tokens)
            idf = math.log(N / df) if df > 0 else 0
            idf_values.append(idf)
        return idf_values

    def compute_idf_smoothed(self):
        """Smooth IDF - 2 doküman için daha iyi"""
        N = 2
        idf_values = []
        for word in self.vocab:
            df = sum(1 for tokens in [self.tokens1, self.tokens2] if word in tokens)
            # Smoothed IDF: log((N + 1) / (df + 1)) + 1
            idf = math.log((N + 1) / (df + 1)) + 1
            idf_values.append(idf)
        return idf_values

    def cosine_similarity_tfidf(self, use_smoothed_idf=True):
        """TF-IDF tabanlı cosine similarity"""
        if use_smoothed_idf:
            idf = self.compute_idf_smoothed()
        else:
            idf = self.compute_idf_standard()

        tf1 = self.compute_tf(self.tokens1)
        tf2 = self.compute_tf(self.tokens2)

        vec1 = [t * i for t, i in zip(tf1, idf)]
        vec2 = [t * i for t, i in zip(tf2, idf)]

        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        return dot / (mag1 * mag2) if mag1 and mag2 else 0.0

    def cosine_similarity_tf(self):
        """Sadece TF tabanlı cosine similarity (IDF olmadan)"""
        tf1 = self.compute_tf(self.tokens1)
        tf2 = self.compute_tf(self.tokens2)

        dot = sum(a * b for a, b in zip(tf1, tf2))
        mag1 = math.sqrt(sum(a * a for a in tf1))
        mag2 = math.sqrt(sum(b * b for b in tf2))

        return dot / (mag1 * mag2) if mag1 and mag2 else 0.0

    def jaccard_similarity(self):
        """Jaccard similarity - basit ama etkili"""
        set1 = set(self.tokens1)
        set2 = set(self.tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def overlap_coefficient(self):
        """Overlap coefficient - küçük dokümanlar için iyi"""
        set1 = set(self.tokens1)
        set2 = set(self.tokens2)
        
        intersection = len(set1.intersection(set2))
        smaller_set = min(len(set1), len(set2))
        
        return intersection / smaller_set if smaller_set > 0 else 0.0

    def get_all_similarities(self):
        """Tüm benzerlik metriklerini döndür"""
        return {
            'cosine_tf': self.cosine_similarity_tf(),
            'cosine_tfidf_standard': self.cosine_similarity_tfidf(use_smoothed_idf=False),
            'cosine_tfidf_smoothed': self.cosine_similarity_tfidf(use_smoothed_idf=True),
            'jaccard': self.jaccard_similarity(),
            'overlap': self.overlap_coefficient()
        }

# Test fonksiyonu
def test_all_methods():
    test_cases = [
        ("hello world", "hello world", "Aynı metinler"),
        ("hello world", "hello universe", "Benzer metinler (1 ortak kelime)"),
        ("hello world", "goodbye moon", "Farklı metinler (ortak kelime yok)"),
        ("the cat sat on the mat", "the dog sat on the mat", "Çok benzer metinler"),
        ("python programming", "python coding", "Benzer terimler"),
        ("artificial intelligence", "machine learning", "İlgili ama farklı")
    ]
    
    for doc1, doc2, description in test_cases:
        print(f"\n=== {description} ===")
        print(f"Doc1: '{doc1}'")
        print(f"Doc2: '{doc2}'")
        
        sim = TextSimilarity(doc1, doc2)
        similarities = sim.get_all_similarities()
        
        for method, score in similarities.items():
            print(f"{method:25}: {score:.4f}")

if __name__ == "__main__":
    test_all_methods()