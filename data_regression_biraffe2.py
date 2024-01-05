import glob
import os
import numpy as np
from torch.utils.data import Dataset
import pandas as pd


class Biraffe2Dataset(Dataset):
    def __init__(self, data_path: str):
        self.X = []
        self.Y = []
        self.y_labels = ["VALENCE", "AROUSAL"]

        files = self.get_files(os.path.join(data_path, "train_data"))
        for file in files:
            dataframe = pd.read_csv(file)
            self.x_labels = [col for col in dataframe.columns.tolist() if col not in self.y_labels]
            self.X.append(dataframe[self.x_labels].values)
            self.Y.append(dataframe[self.y_labels].values)

        self.X = np.concatenate(self.X, axis=0)
        self.Y = np.concatenate(self.Y, axis=0)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]

    def get_files(self, data_path: str) -> list[str]:
        return glob.glob(os.path.join(data_path, "*.csv"))
