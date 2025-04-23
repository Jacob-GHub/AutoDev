from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from utils.embedding import embed_code

def plot(examples):
    snippets = [s for s, _ in examples]
    embeddings = [embed_code(s) for s in snippets]

    pca = PCA(n_components=2)
    reduced = pca.fit_transform(embeddings)

    for (x, y), text in zip(reduced, snippets):
        plt.scatter(x, y)
        plt.text(x + 0.01, y + 0.01, text[:20] + "...", fontsize=9)

    plt.title("2D Projection of Code Embeddings")
    plt.show()
