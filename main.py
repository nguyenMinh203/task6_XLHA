import numpy as np
from collections import defaultdict
from math import log2
import matplotlib.pyplot as plt


# Hàm đọc dữ liệu IRIS
def load_data(path):
    data = []
    labels = []
    with open(path, 'r') as file:
        for line in file:
            if line.strip():
                values = line.strip().split(',')
                data.append([float(v) for v in values[:-1]])
                labels.append(values[-1])
    return np.array(data), labels


# Khởi tạo centroids ngẫu nhiên
def initialize_centroids(data, k):
    np.random.seed(42)
    indices = np.random.choice(data.shape[0], k, replace=False)
    return data[indices]


# Tính khoảng cách Euclidean
def euclidean_distance(point1, point2):
    return np.sqrt(np.sum((point1 - point2) ** 2))


# Gán mỗi điểm vào cụm gần nhất
def assign_clusters(data, centroids):
    clusters = defaultdict(list)
    for idx, point in enumerate(data):
        distances = [euclidean_distance(point, centroid) for centroid in centroids]
        cluster = np.argmin(distances)
        clusters[cluster].append(idx)
    return clusters


# Cập nhật các centroid dựa trên trung bình của các điểm thuộc cụm
def update_centroids(data, clusters, k):
    new_centroids = []
    for i in range(k):
        if clusters[i]:  # Nếu cụm không trống
            new_centroids.append(np.mean(data[clusters[i]], axis=0))
        else:  # Nếu cụm trống, khởi tạo centroid ngẫu nhiên mới
            new_centroids.append(data[np.random.choice(len(data))])
    return np.array(new_centroids)


# Thuật toán K-means chính
def k_means(data, k, max_iters=100, tolerance=1e-4):
    centroids = initialize_centroids(data, k)
    for _ in range(max_iters):
        clusters = assign_clusters(data, centroids)
        new_centroids = update_centroids(data, clusters, k)
        if np.allclose(centroids, new_centroids, atol=tolerance):
            break
        centroids = new_centroids
    return clusters, centroids


# Chuyển đổi kết quả phân cụm thành nhãn cho từng điểm
def get_labels_from_clusters(clusters, n_samples):
    labels = np.empty(n_samples, dtype=int)
    for cluster_idx, points in clusters.items():
        for point_idx in points:
            labels[point_idx] = cluster_idx
    return labels


# Hàm tính F1-score (macro)
def f1_score_macro(true_labels, predicted_labels):
    unique_labels = set(true_labels)
    f1_scores = []
    for label in unique_labels:
        tp = sum((predicted_labels == label) & (true_labels == label))
        fp = sum((predicted_labels == label) & (true_labels != label))
        fn = sum((predicted_labels != label) & (true_labels == label))
        if tp == 0:
            f1 = 0
        else:
            precision = tp / (tp + fp)
            recall = tp / (tp + fn)
            f1 = 2 * (precision * recall) / (precision + recall)
        f1_scores.append(f1)
    return np.mean(f1_scores)


# Hàm tính RAND Index
def rand_index(true_labels, predicted_labels):
    tp = tn = fp = fn = 0
    for i in range(len(true_labels)):
        for j in range(i + 1, len(true_labels)):
            same_cluster = (predicted_labels[i] == predicted_labels[j])
            same_class = (true_labels[i] == true_labels[j])
            tp += same_cluster and same_class
            tn += not same_cluster and not same_class
            fp += same_cluster and not same_class
            fn += not same_cluster and same_class
    return (tp + tn) / (tp + tn + fp + fn)


# Hàm tính NMI
def normalized_mutual_info(true_labels, predicted_labels):
    total = len(true_labels)
    labels_true, labels_pred = set(true_labels), set(predicted_labels)
    mi = 0
    for label in labels_true:
        for cluster in labels_pred:
            intersect = sum((true_labels == label) & (predicted_labels == cluster))
            if intersect > 0:
                mi += intersect / total * log2((intersect * total) /
                                               (sum(true_labels == label) * sum(predicted_labels == cluster)))
    h_true = -sum((sum(true_labels == label) / total) * log2(sum(true_labels == label) / total)
                  for label in labels_true if sum(true_labels == label) > 0)
    h_pred = -sum((sum(predicted_labels == cluster) / total) * log2(sum(predicted_labels == cluster) / total)
                  for cluster in labels_pred if sum(predicted_labels == cluster) > 0)
    return mi / np.sqrt(h_true * h_pred) if h_true and h_pred else 0


# Hàm tính DB Index
def davies_bouldin_index(data, labels):
    unique_labels = np.unique(labels)
    cluster_means = [np.mean(data[labels == label], axis=0) for label in unique_labels if
                     len(data[labels == label]) > 0]
    s = [np.mean([euclidean_distance(x, cluster_means[i]) for x in data[labels == label]])
         for i, label in enumerate(unique_labels) if len(data[labels == label]) > 0]

    if len(cluster_means) == 0 or len(s) == 0:
        return float('inf')  # or some other suitable value or handling

    db = 0.0
    for i in range(len(cluster_means)):
        max_r = max([(s[i] + s[j]) / euclidean_distance(cluster_means[i], cluster_means[j])
                     for j in range(len(cluster_means)) if i != j], default=0)
        db += max_r
    return db / len(cluster_means)


# Đường dẫn dữ liệu
data, true_labels = load_data('C:\\Users\\Admin\\PycharmProjects\\bth6\\input\\iris.data')

# Chuyển đổi nhãn thực thành số
label_map = {label: idx for idx, label in enumerate(set(true_labels))}
true_numeric_labels = np.array([label_map[label] for label in true_labels])

# Lists to store the results
f1_scores = []
rand_indices = []
nmis = []
db_indices = []

# Lặp qua các giá trị k từ 1 đến 5 và lưu kết quả
for k in range(1, 6):
    print(f"\nK = {k}")
    clusters, centroids = k_means(data, k)
    predicted_labels = get_labels_from_clusters(clusters, data.shape[0])

    # Tính toán các độ đo
    f1 = f1_score_macro(true_numeric_labels, predicted_labels)
    rand_idx = rand_index(true_numeric_labels, predicted_labels)
    nmi = normalized_mutual_info(true_numeric_labels, predicted_labels)
    db_index = davies_bouldin_index(data, predicted_labels)

    # Lưu kết quả
    f1_scores.append(f1)
    rand_indices.append(rand_idx)
    nmis.append(nmi)
    db_indices.append(db_index)

    # In kết quả
    print("F-measure (F1-score):", f1)
    print("Chỉ số RAND:", rand_idx)
    print("NMI (Thông tin hỗn hợp chuẩn hóa):", nmi)
    print("Chỉ số DB (Davies-Bouldin):", db_index)

# Vẽ biểu đồ
plt.figure(figsize=(12, 8))
plt.plot(range(1, 6), f1_scores, label='F1 Score', marker='o')
plt.plot(range(1, 6), rand_indices, label='RAND Index', marker='o')
plt.plot(range(1, 6), nmis, label='NMI', marker='o')
plt.plot(range(1, 6), db_indices, label='DB Index', marker='o')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Score')
plt.title('Clustering Evaluation Metrics')
plt.xticks(range(1, 6))
plt.legend()
plt.grid()
plt.show()
