# utils/monitoring.py
import prometheus_client
from prometheus_client import Gauge, start_http_server

accuracy_gauge = Gauge('model_accuracy', 'Accuracy of model', ['model_name'])
auc_gauge = Gauge('model_roc_auc', 'ROC AUC of model', ['model_name'])

def start_metrics_server(port=8000):
    start_http_server(port)

def update_metrics(model_name, accuracy, roc_auc):
    accuracy_gauge.labels(model_name=model_name).set(accuracy)
    auc_gauge.labels(model_name=model_name).set(roc_auc)
