# ProjectCare: Advanced Medical Data Analysis & Predictive Machine Learning Portal

## Link to download the dmg standalone file (MacOS only): https://github.com/javiNguema/HealthEvolPredict/blob/e09b4b4a4105aacd7d04b897e3fd6f5c4e53a6d5/ProjectCare_Setup.dmg

ProjectCare is a secure, standalone desktop application built in Python designed to empower healthcare researchers and data scientists with a comprehensive suite for exploratory data analysis, feature engineering, and automated machine learning classification.

The core philosophy of ProjectCare is complete data flexibility and absolute privacy. Rather than being locked into a single dataset or depending on cloud APIs, the application allows users to ingest any custom clinical dataset to analyze data locally, train models, and run local AI-driven insights.

## Key Application Modules 
1. Local AI Chatbot Data Assistant (Powered by Ollama)
To bridge the gap between complex raw data structures and intuitive insights without compromising data privacy, ProjectCare features an integrated conversational AI chatbot running completely on the user's local machine:

Privacy-First Architecture: Powered by a local Ollama deployment engine, ensuring that clinical records and sensitive patient datasets never leave the local environment or touch external cloud servers.

Human-Readable Data Exploration: Users can query, audit, and interrogate their active datasets using natural conversational language through a sleek, responsive chat interface.

Intelligent Pre-Training Diagnostics: The chatbot dynamically scans loaded data attributes, allowing clinicians and researchers to verify distributions, find missing values, and gain an empirical understanding of their cohort before launching model training pipelines.

2. Advanced Visualization & Pre-Training Analysis
To ensure optimal feature selection before running computationally expensive training algorithms, ProjectCare includes advanced statistical and mathematical analytics tools:

Principal Component Analysis (PCA): Reduce dataset dimensionality, identify variance distribution, and project high-dimensional clinical features into principal components to easily visualize group separations.

Correlation Matrix Heatmaps: Instantly compute and plot correlation coefficients across all numerical variables to detect multi-collinearity, allowing users to strip redundant or highly correlated inputs before training.

3. Universal ML Training Engine
Data-Agnostic Classification: Load any structured dataset (including physiological vitals, lab results, or demographic matrices).

Automated Pipelines: Leverages PyCaret and Imbalanced-Learn (utilizing SMOTE techniques) to handle class imbalances automatically (e.g., rare clinical anomalies or low-incidence conditions).

Model Validation: Generates comprehensive classification metrics, confusion matrices, and feature importance rankings directly within the GUI workspace.

4. Model Lifecycle & Persistence Management
Save and Export Models: Once a high-performing classification model is trained, users can export and save the serialized model state directly through the interface.

Data-Independent Predictions: Crucial for long-term deployment. If a user no longer has access to the original raw training dataset, they can simply load a previously saved model file (.pkl) into the app to run real-time predictions on new, individual patient records.

5. Secure Authentication & Operations Gateway
Dynamic Database Navigator: Built-in tree view explorer that queries remote schemas in real-time, displays metadata tables matching the pcare_ signature, and streams data records smoothly using non-blocking asynchronous background threads.

Pure-Python Database Driver: Powered by pure-Python pymysql drivers, ensuring full application compatibility within sandboxed environments (like macOS .app bundles) without throwing authentication plugin or native C-library path errors.

Local Mode Standby: A secure login layout featuring a backup local Guest mode bypass if the remote server is unreachable.
