# utils/explainability.py
import shap
import lime
from lime.lime_tabular import LimeTabularExplainer

class SHAPExplainerManager:
    def __init__(self, model, data_sample):
        self.model = model
        self.explainer = shap.Explainer(model, data_sample)
    def get_shap_values(self, X):
        return self.explainer(X)

class LIMEExplainer:
    def __init__(self, training_data, feature_names):
        self.explainer = LimeTabularExplainer(training_data, feature_names=feature_names, class_names=['Down','Up'], discretize_continuous=True)
    def explain_instance(self, instance, predict_fn):
        return self.explainer.explain_instance(instance, predict_fn)
