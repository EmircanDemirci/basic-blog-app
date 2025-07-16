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
        self.idf = self.compute_idf()

    def tokenize(self, text):
        if isinstance(text, list):
            text = " ".join(text)
        return re.findall(r'\b\w+\b', text.lower())

    def compute_tf(self, tokens):
        if not tokens:
            return [0] * len(self.vocab)

        counts = Counter(tokens)
        return [counts[word] / len(tokens) for word in self.vocab]

    def compute_idf(self):
        N = 2  # İki doküman var
        idf_values = []
        for word in self.vocab:
            df = 0
            if word in self.tokens1:
                df += 1
            if word in self.tokens2:
                df += 1
            
            # DÜZELTİLEN IDF FORMÜLÜ: log(N / df) 
            # Orijinal kodda log(N / (1 + df)) kullanılıyordu ki bu yanlıştı
            if df > 0:  # df her zaman > 0 olacak çünkü vocab'taki kelimeler en az bir dokümanda var
                idf = math.log(N / df)
            else:
                idf = 0  # Bu duruma hiç girmeyecek ama güvenlik için
            idf_values.append(idf)
        return idf_values

    def compute_tfidf(self, tokens):
        tf = self.compute_tf(tokens)
        return [t * i for t, i in zip(tf, self.idf)]

    def cosine_similarity(self):
        vec1 = self.compute_tfidf(self.tokens1)
        vec2 = self.compute_tfidf(self.tokens2)

        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        return dot / (mag1 * mag2) if mag1 and mag2 else 0.0

# Test fonksiyonu
def test_similarity():
    # Test 1: Aynı metinler
    sim1 = TextSimilarity("hello world", "hello world")
    print(f"Aynı metinler: {sim1.cosine_similarity():.4f}")
    
    # Test 2: Benzer metinler
    sim2 = TextSimilarity("hello world", "hello universe")
    print(f"Benzer metinler: {sim2.cosine_similarity():.4f}")
    
    # Test 3: Farklı metinler
    sim3 = TextSimilarity("hello world", "goodbye moon")
    print(f"Farklı metinler: {sim3.cosine_similarity():.4f}")
    
    # Test 4: Tamamen farklı metinler
    sim4 = TextSimilarity("cat dog", "house car")
    print(f"Tamamen farklı: {sim4.cosine_similarity():.4f}")

if __name__ == "__main__":
    test_similarity()