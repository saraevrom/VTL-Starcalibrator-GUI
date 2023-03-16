import matplotlib.pyplot as plt
import numpy as np

def plot_roc(y_pred, y_true, npoints):
    y_pred_flat = y_pred.flatten()
    y_true_flat = y_true.flatten() > 0.5
    ny_true_flat = np.logical_not(y_true_flat)
    positives = y_true_flat.sum()
    negatives = y_true_flat.shape[0]-positives

    thresholds = np.linspace(0.0, 1.0, npoints)
    fprs = []
    tprs = []
    for thresh in thresholds:
        pred_pos = (y_pred_flat > thresh)
        tp = np.logical_and(pred_pos, y_true_flat).sum()
        fp = np.logical_and(pred_pos, ny_true_flat).sum()

        fprs.append(fp/negatives)
        tprs.append(tp/positives)

    fig, ax = plt.subplots()
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.plot(fprs, tprs, color="black")
    ax.plot([0,1], [0,1], "--", color="gray")

    fig.show()
