import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List, Optional
import tensorflow as tf

# Scikit-learn para modelos independientes
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# PyCaret para análisis automatizado
import pycaret.classification as pc

def preprocess_selected_features(df: pd.DataFrame, features: List[str], target: str, col_missing_threshold: float = 0.50) -> Optional[pd.DataFrame]:
    """
    Filtra el DataFrame usando únicamente las variables (X) y el target (Y) seleccionados.
    Aplica la política estricta de descarte de nulos sin extrapolaciones artificiales.
    """
    if df is None or df.empty or not features or not target:
        return None

    # Asegurar que todas las columnas solicitadas existan en el DataFrame cargado
    all_requested_cols = list(set(features + [target]))
    available_cols = [col for col in all_requested_cols if col in df.columns]
    
    if target not in available_cols or len(available_cols) < 2:
        return None

    # Aislar matriz de trabajo numérica
    working_df = df[available_cols].copy()
    working_df = working_df.select_dtypes(include=[np.number])
    
    if target not in working_df.columns:
        # El target debe ser numérico o codificado para estos clasificadores
        return None

    # Tratamiento seguro de infinitos
    working_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # 1. Descartar columnas individuales si superan el umbral crítico de datos ausentes
    missing_proportions = working_df.isna().mean()
    valid_cols = missing_proportions[missing_proportions <= col_missing_threshold].index.tolist()
    
    if target not in valid_cols:
        return None
        
    working_df = working_df[valid_cols]

    # 2. Eliminar filas con nulos esporádicos restantes (Dropping seguro)
    cleaned_df = working_df.dropna()

    if cleaned_df.shape[0] < 5: # Verificación de registros mínimos para entrenar
        return None

    return cleaned_df


def run_pycaret_pipeline(df: pd.DataFrame, features: List[str], target_col: str, checked_metrics: List[str]) -> Tuple[Any, pd.DataFrame, Dict[str, Any]]:
    """
    Inicializa PyCaret, extrae el mejor modelo y la tabla de resultados.
    Retorna los datos numéricos crudos para graficar en la UI, evitando retardos de renderizado.
    """
    from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve
    
    cleaned_df = preprocess_selected_features(df, features, target_col)
    if cleaned_df is None:
        raise ValueError("Registros insuficientes tras filtrar las variables seleccionadas.")

    # 1. Inicializar setup de PyCaret
    session = pc.setup(
        data=cleaned_df,
        target=target_col,
        train_size=0.8,
        preprocess=True,
        numeric_imputation='drop',
        categorical_imputation='drop',
        html=False,
        verbose=False,
        profile=False
    )

    # 2. Configurar métrica de ordenamiento
    metric_map = {"Accuracy": "Accuracy", "AUC": "AUC", "Recall": "Recall", "Precision": "Precision", "F1-Score": "F1"}
    primary_metric = "Accuracy"
    if checked_metrics:
        for m in checked_metrics:
            if m in metric_map:
                primary_metric = metric_map[m]
                break

    # 3. Obtener el mejor modelo clasificador (Sin paralelismo destructivo)
    best_model = pc.compare_models(sort=primary_metric, verbose=False)
    metrics_table = pc.pull()
    
    # 4. Extraer los conjuntos de prueba (Test) que PyCaret guardó internamente
    X_test = pc.get_config('X_test')
    y_test = pc.get_config('y_test')
    
    # 5. Construir el diccionario de datos puros de curvas
    plot_data_dict = {}
    try:
        preds = best_model.predict(X_test) # type: ignore
        
        # A. Datos de la Matriz de Confusión
        plot_data_dict['confusion_matrix'] = (y_test.values, preds)
        
        # B. Datos de las curvas ROC y Precision-Recall (si el modelo soporta probabilidades)
        if hasattr(best_model, "predict_proba"):
            probs = best_model.predict_proba(X_test)[:, 1] # type: ignore
            
            fpr, tpr, _ = roc_curve(y_test, probs)
            plot_data_dict['auc'] = (fpr, tpr)
            
            precision, recall, _ = precision_recall_curve(y_test, probs)
            plot_data_dict['pr'] = (recall, precision) # X: recall, Y: precision
            
        # C. Datos de Importancia de Variables
        if hasattr(best_model, "feature_importances_"):
            plot_data_dict['feature'] = (X_test.columns.tolist(), best_model.feature_importances_) # type: ignore
        elif hasattr(best_model, "coef_"):
            plot_data_dict['feature'] = (X_test.columns.tolist(), np.abs(best_model.coef_[0])) # type: ignore
            
    except Exception as e:
        print(f"Aviso al extraer matriz de datos analíticos: {e}")

    return best_model, metrics_table, plot_data_dict


def run_custom_scikit_model(df: pd.DataFrame, features: List[str], target_col: str, algo_name: str, params: Dict[str, Any]) -> Tuple[Dict[str, float], List[str], Any, List[str], List[str]]:
    """
    Entrena un clasificador Scikit-Learn basado estrictamente en la selección X e Y de la UI.
    """
    cleaned_df = preprocess_selected_features(df, features, target_col)
    if cleaned_df is None:
        raise ValueError("Variables seleccionadas sin suficientes muestras válidas tras la limpieza.")

    # Separar variables predictoras del vector objetivo
    actual_features = [col for col in cleaned_df.columns if col != target_col]
    X = cleaned_df[actual_features]
    y = cleaned_df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() >= 2 else None
    )

    if "Bosques Aleatorios" in algo_name:
        n_est = int(params.get("n_estimators", 100))
        max_d = params.get("max_depth", None)
        max_depth = int(max_d) if max_d and str(max_d).lower() != "none" else None
        model = RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, random_state=42)
        
    elif "Máquinas de Vector" in algo_name:
        kernel_val = params.get("kernel", "rbf")
        model = SVC(kernel=kernel_val, probability=True, random_state=42)
        
    elif "K-Vecinos" in algo_name:
        k_val = int(params.get("n_neighbors", 5))
        model = KNeighborsClassifier(n_neighbors=k_val)
        
    else:
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(max_iter=1000)

    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_test)[:, 1] # type: ignore
        try:
            auc_v = roc_auc_score(y_test, probs)
        except:
            auc_v = 0.0
    else:
        auc_v = 0.0

    metrics = {
        "Accuracy": accuracy_score(y_test, preds),
        "Precision": precision_score(y_test, preds, zero_division=0),
        "Recall": recall_score(y_test, preds, zero_division=0),
        "F1-Score": f1_score(y_test, preds, zero_division=0),
        "AUC": auc_v
    }

    importance_list = []
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_ # type: ignore
        indices = np.argsort(importances)[::-1]
        for idx in indices:
            importance_list.append(f"{actual_features[idx]}: {importances[idx]:.4f}")

    return metrics, importance_list, model, X_test, y_test







def multilayer_perceptron(self, df: pd.DataFrame, features: List[str], target_col: str) -> Tuple[Dict[str, float], List[str], Any, List[str], List[str]]:
    """
    Implementación de un clasificador Multilayer Perceptron (MLP) usando Scikit-Learn.
    """
    from sklearn.neural_network import MLPClassifier
    
    cleaned_df = preprocess_selected_features(df, features, target_col)
    if cleaned_df is None:
        raise ValueError("Variables seleccionadas sin suficientes muestras válidas tras la limpieza.")

    actual_features = [col for col in cleaned_df.columns if col != target_col]
    X = cleaned_df[actual_features]
    y = cleaned_df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() >= 2 else None
    )

    model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=300, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_test)[:, 1] # type: ignore
        try:
            auc_v = roc_auc_score(y_test, probs)
        except:
            auc_v = 0.0
    else:
        auc_v = 0.0

    metrics = {
        "Accuracy": accuracy_score(y_test, preds),
        "Precision": precision_score(y_test, preds, zero_division=0),
        "Recall": recall_score(y_test, preds, zero_division=0),
        "F1-Score": f1_score(y_test, preds, zero_division=0),
        "AUC": auc_v
    }

    importance_list = []
    if hasattr(model, "coefs_"):
        coefs = np.mean(np.abs(model.coefs_[0]), axis=1) # type: ignore
        indices = np.argsort(coefs)[::-1]
        for idx in indices:
            importance_list.append(f"{actual_features[idx]}: {coefs[idx]:.4f}")

    return metrics, importance_list, model, X_test, y_test

