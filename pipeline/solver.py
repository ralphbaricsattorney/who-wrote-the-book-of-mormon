"""Elastic-net multinomial logistic regression, solved by accelerated proximal gradient (FISTA).

Same model and objective as sklearn's LogisticRegression(C, l1_ratio, solver="saga"):

    minimize  C * sum_i w_i * cross_entropy_i  +  l1_ratio * |W|_1  +  (1 - l1_ratio)/2 * |W|_2^2

with an unpenalized intercept. sklearn's saga needs ~30 s per fit here and stops unconverged; this
converges in about a second and can warm-start along a path of C values.

A fit records `converged_` and `residual_`. Callers must check them: fit() never raises on its own.
"""
import numpy as np
from scipy.special import log_softmax, softmax


class ElasticNetLogit:
    def __init__(self, C: float, l1_ratio: float, max_iter: int = 2000, tol: float = 1e-4):
        self.C, self.l1_ratio, self.max_iter, self.tol = C, l1_ratio, max_iter, tol

    def fit(self, X, y, sample_weight=None, init: "ElasticNetLogit | None" = None):
        X = np.asarray(X, dtype=np.float64)
        n, p = X.shape
        self.classes_, yi = np.unique(y, return_inverse=True)
        k = len(self.classes_)
        w = np.ones(n) if sample_weight is None else np.asarray(sample_weight, dtype=np.float64)
        Y = np.eye(k)[yi] * w[:, None]
        l1, l2 = self.l1_ratio / self.C, (1 - self.l1_ratio) / self.C      # objective divided through by C

        # Step size from a bound on the curvature of the loss: 0.5 * largest eigenvalue of [X,1]' diag(w) [X,1]
        A = np.hstack([X, np.ones((n, 1))]) * np.sqrt(w)[:, None]
        step = 1 / (0.5 * np.linalg.norm(A, 2) ** 2 + l2)

        W = np.zeros((p, k)) if init is None else init.coef_.T.copy()
        b = np.zeros(k) if init is None else init.intercept_.copy()
        Wm, bm, t = W.copy(), b.copy(), 1.0                                # momentum point
        for self.n_iter_ in range(1, self.max_iter + 1):
            R = softmax(X @ Wm + bm, axis=1) * w[:, None] - Y              # weighted residuals
            V = Wm - step * (X.T @ R + l2 * Wm)
            W_new = np.sign(V) * np.maximum(np.abs(V) - step * l1, 0)      # soft threshold: the L1 part
            b_new = bm - step * R.sum(0)
            if np.vdot(Wm - W_new, W_new - W) > 0:                         # momentum overshot: restart it
                t = 1.0
            t_new = (1 + np.sqrt(1 + 4 * t * t)) / 2
            Wm_old, bm_old = Wm, bm
            Wm = W_new + (t - 1) / t_new * (W_new - W)
            bm = b_new + (t - 1) / t_new * (b_new - b)
            # Converged when the largest (proximal) gradient entry, per training row, is below tol
            gradient = max(np.abs(W_new - Wm_old).max(), np.abs(b_new - bm_old).max()) / step
            W, b, t = W_new, b_new, t_new
            if gradient < self.tol * n:
                break
        self.coef_, self.intercept_ = W.T, b
        self.residual_ = gradient / n                 # largest gradient entry per training row at the end
        self.converged_ = self.residual_ < self.tol
        return self

    def decision_function(self, X) -> np.ndarray:
        return np.asarray(X, dtype=np.float64) @ self.coef_.T + self.intercept_

    def predict_proba(self, X) -> np.ndarray:
        return softmax(self.decision_function(X), axis=1)

    def predict_log_proba(self, X) -> np.ndarray:
        return log_softmax(self.decision_function(X), axis=1)

    def objective(self, X, y, sample_weight) -> float:
        yi = np.searchsorted(self.classes_, y)
        nll = -(sample_weight * self.predict_log_proba(X)[np.arange(len(yi)), yi]).sum()
        return self.C * nll + self.l1_ratio * np.abs(self.coef_).sum() + (1 - self.l1_ratio) / 2 * (self.coef_ ** 2).sum()
