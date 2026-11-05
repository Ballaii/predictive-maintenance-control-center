import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
    f1_score, log_loss, precision_recall_curve, precision_score, recall_score, roc_auc_score,
    roc_curve,
)


def select_threshold(y_true: np.ndarray, scores: np.ndarray) -> dict:
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    eligible = np.flatnonzero(precision[:-1] >= 0.90)
    if len(eligible):
        chosen = eligible[np.argmax(recall[:-1][eligible])]
        method = "maximum recall at validation precision >= 0.90"
    else:
        f1 = np.divide(
            2 * precision[:-1] * recall[:-1], precision[:-1] + recall[:-1],
            out=np.zeros_like(precision[:-1]), where=(precision[:-1] + recall[:-1]) > 0,
        )
        chosen = int(np.argmax(f1))
        method = "fallback: best validation F1 (90% precision unavailable)"
    return {
        "threshold": float(thresholds[chosen]), "method": method,
        "precision": float(precision[chosen]), "recall": float(recall[chosen]),
        "precision_target_achieved": bool(len(eligible)),
        "predicted_positives": int((scores >= thresholds[chosen]).sum()),
    }


def evaluate_scores(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    predicted = (scores >= threshold).astype(int)
    matrix = confusion_matrix(y_true, predicted, labels=[0, 1])
    precision, recall, pr_thresholds = precision_recall_curve(y_true, scores)
    fpr, tpr, _ = roc_curve(y_true, scores)
    fraction, mean = calibration_curve(y_true, scores, n_bins=10, strategy="quantile")
    return {
        "accuracy": float(accuracy_score(y_true, predicted)),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "average_precision": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "brier_score": float(brier_score_loss(y_true, scores)),
        "log_loss": float(log_loss(y_true, scores, labels=[0, 1])),
        "threshold": threshold, "confusion_matrix": matrix.tolist(),
        "false_positives": int(matrix[0, 1]), "false_negatives": int(matrix[1, 0]),
        "pr_curve": {"precision": precision.tolist(), "recall": recall.tolist(),
                     "thresholds": pr_thresholds.tolist()},
        "roc_curve": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "calibration": {"predicted": mean.tolist(), "observed": fraction.tolist()},
    }
