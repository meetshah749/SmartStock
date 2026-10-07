# SmartStock AI — Machine Learning Pipeline

This module hosts the model training, feature engineering, and inference pipelines for stock market price directional prediction.

## Folder Layout

```
ml/
├── data/               # Raw and preprocessed feature stores
├── preprocessing/      # Technical indicator calculators (RSI, MACD, SMA, EMA)
├── features/           # Feature selection and transformation rules
├── training/           # Train/Validation time-series split scripts
├── evaluation/         # Calibration & metric evaluation scripts (Accuracy, ROC-AUC)
└── models/             # Serialized model artifacts (.json / .pkl) & SHAP explainers
```
