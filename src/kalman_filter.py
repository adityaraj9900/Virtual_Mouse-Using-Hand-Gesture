import numpy as np


class KalmanFilter2D:
    """2D Kalman filter for buttery-smooth cursor movement."""

    def __init__(self, process_noise=1e-4, measurement_noise=0.05):
        # State vector: [x, y, vx, vy]
        self.state = np.zeros(4)
        self.P = np.eye(4) * 1000.0

        dt = 1.0
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1,  0],
            [0, 0, 0,  1],
        ], dtype=float)

        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=float)

        self.Q = np.eye(4) * process_noise
        self.R = np.eye(2) * measurement_noise
        self.initialized = False

    def update(self, x, y):
        measurement = np.array([float(x), float(y)])

        if not self.initialized:
            self.state = np.array([float(x), float(y), 0.0, 0.0])
            self.initialized = True
            return int(x), int(y)

        # Predict step
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q

        # Update step
        y_res = measurement - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.state = self.state + K @ y_res
        self.P = (np.eye(4) - K @ self.H) @ self.P

        return int(self.state[0]), int(self.state[1])

    def reset(self):
        self.state = np.zeros(4)
        self.P = np.eye(4) * 1000.0
        self.initialized = False
