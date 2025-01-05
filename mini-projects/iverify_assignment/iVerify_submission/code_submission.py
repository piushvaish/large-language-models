# Load Libraries
import pandas as pd
import numpy as np
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import plotly.express as px
from umap import UMAP
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
from sklearn.preprocessing import StandardScaler

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
warnings.filterwarnings("ignore")

# Load Data
df = pd.read_csv("pseudoProcess.csv")

# EDA
df.info()

df.head()

# Check for missing values
print(df.isnull().sum())

## pid null?
df[df["pid"].isna()].sample(10)

# Convert timestamp to datetime
df["readableTimestamp"] = pd.to_datetime(df["readableTimestamp"])
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

print(df["readableTimestamp"].min())
print(df["timestamp"].min())

# Check for these timestamps

df["readableTimestamp"].dt.year.value_counts()

# Remove date before 2024
df = df[df["readableTimestamp"].dt.year >= 2024]

# Ensure PID is an integer
df["pid"] = pd.to_numeric(df["pid"], errors="coerce")

# Handle missing or incorrect data (here we drop missing)
df = df.dropna()

print(df.info())

# Basic info about the dataset
print(f"Total rows: {len(df)}")
print(f"Number of unique devices: {df['device'].nunique()}")
print(f"Number of unique scans: {df['scan'].nunique()}")
print(f"Number of unique iOS versions: {df['iOSVersion'].nunique()}")
print(f"Number of unique pid: {df['pid'].nunique()}")
print(f"Number of unique process names: {df['procName'].nunique()}")

# Devices and scans
device_scan_counts = df.groupby("device")["scan"].nunique()
print(f"\nAverage scans per device: {device_scan_counts.mean():.2f}")
print(f"Max scans for a device: {device_scan_counts.max()}")
print(f"Min scans for a device: {device_scan_counts.min()}")

# iOS versions
ios_versions = df["iOSVersion"].value_counts()
print("\nTop 5 iOS versions:")
print(ios_versions.head())

# Analyze process names
process_counts = df["procName"].value_counts()
print(f"\nTotal unique process names: {len(process_counts)}")
print("\nTop 10 most common processes:")
print(process_counts.head(10))

# Analyze processes per scan
processes_per_scan = df.groupby(["device", "scan"])["procName"].count()
print("\nSummary of processes per scan:")
print(processes_per_scan.describe())

# Check for scans with only one process
single_process_scans = processes_per_scan[processes_per_scan == 1]
print(f"\nNumber of scans with only one process: {len(single_process_scans)}")
if len(single_process_scans) > 0:
    print("Scans with only one process:")
    print(single_process_scans)


# Check for multiple process lists within a scan
def check_multiple_lists(group):
    timestamps = group["readableTimestamp"].nunique()
    return timestamps > 1


multiple_lists = df.groupby(["device", "scan"]).apply(check_multiple_lists)
print(f"\nNumber of scans with multiple process lists: {multiple_lists.sum()}")
if multiple_lists.sum() > 0:
    print("Scans with multiple process lists:")
    print(multiple_lists[multiple_lists].head())

# Identify rare processes
rare_processes = process_counts[process_counts == 1].index.tolist()
print(f"\nNumber of rare processes (appearing only once): {len(rare_processes)}")
print("Sample of rare processes:", rare_processes[:10])

# Time-based analysis
df["date"] = df["timestamp"].dt.date
# Number of processes over time
plt.figure(figsize=(14, 7))
temp_df = df.groupby("date").size().reset_index(name="count")

fig = px.line(
    temp_df,
    x="date",
    y="count",
    title="Number of Processes per Day",
    labels={"Date": "Date", "Number of Processes": "Number of Processes"},
    template="plotly_white",
)

# Update layout to follow good data visualization practices
fig.update_layout(
    title={"text": "Number of Processes per Day", "x": 0.5, "xanchor": "center"},
    xaxis_title="Date",
    yaxis_title="Number of Processes",
    xaxis=dict(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all"),
                ]
            )
        ),
        rangeslider=dict(visible=True),
        type="date",
    ),
    yaxis=dict(tickformat=","),
    margin=dict(l=50, r=50, t=50, b=50),
    width=1000,
    height=600,
)

# Show the plot
fig.show()

# Save the plot
fig.write_html("number_processes.html")

# Calculate the number of unique processes per day
daily_process_counts = df.groupby("date")["procName"].nunique().reset_index()
daily_process_counts.columns = ["Date", "UniqueProcesses"]

# Create the bar chart using Plotly Express with color and style options
fig = px.bar(
    daily_process_counts,
    x="Date",
    y="UniqueProcesses",
    title="Unique Processes per Day",
    labels={"Date": "Date", "UniqueProcesses": "Number of Unique Processes"},
    text="UniqueProcesses",
    color="UniqueProcesses",  # Color bars by the count of unique processes
    color_continuous_scale="Viridis",
)  # Choose a color scale

# Customize layout for a more colorful appearance
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Number of Unique Processes",
    plot_bgcolor="white",  # Background color of the plotting area
    paper_bgcolor="white",  # Background color of the entire figure
    title_font=dict(size=20, color="darkblue"),
    xaxis=dict(
        tickangle=-90,  # Angle of x-axis tick labels for better readability
        title_font=dict(size=16),
        tickfont=dict(size=14),
    ),
    yaxis=dict(title_font=dict(size=16), tickfont=dict(size=14)),
    showlegend=False,  # Hide legend if not necessary
)

# Display the bar chart
fig.show()

#
fig.write_html("unique_processes.html")

# Analyze PID distribution
plt.figure(figsize=(12, 6))
plt.hist(df["pid"], bins=50)
plt.title("Distribution of Process IDs")
plt.xlabel("PID")
plt.ylabel("Frequency")
# plt.show()
plt.savefig("pid_distribution.png")
plt.close()


# Treat PIDs as categorical
pid_frequency = df["pid"].value_counts()
print("\nMost common PIDs:")
print(pid_frequency.head())

# Visualize PID frequency
plt.figure(figsize=(12, 6))
pid_frequency.head(20).plot(kind="bar")
plt.title("Frequency of Top 20 PIDs")
plt.xlabel("PID")
plt.ylabel("Frequency")
plt.tight_layout()
# plt.show()
plt.savefig("pid_frequency.png")
plt.close()


# Analyze PID uniqueness within scans
def check_pid_uniqueness(group):
    return group["pid"].nunique() == len(group)


pid_uniqueness = df.groupby(["device", "scan"]).apply(check_pid_uniqueness)
print(f"\nPercentage of scans with all unique PIDs: {pid_uniqueness.mean()*100:.2f}%")


# Analyze PID assignment patterns
def check_pid_linearity(group):
    pids = group["pid"].sort_values()
    diff = pids.diff()
    return (diff != 1).sum() / len(diff)


pid_nonlinearity = df.groupby(["device", "scan"]).apply(check_pid_linearity)
pid_nonlinearity = pid_nonlinearity.reset_index(name="non_linearity_score")

# Create a new column to highlight scores above 0.90
pid_nonlinearity["highlight"] = pid_nonlinearity["non_linearity_score"] > 0.90

# Create the plot
fig = px.scatter(
    pid_nonlinearity,
    x="scan",
    y="non_linearity_score",
    color="device",
    hover_data=["device", "scan", "non_linearity_score"],
    labels={
        "non_linearity_score": "Non-linearity Score",
        "scan": "Scan",
        "device": "Device",
    },
    title="Non-linearity Scores by Device and Scan",
)

# Highlight points with score > 0.90
fig.add_trace(
    px.scatter(
        pid_nonlinearity[pid_nonlinearity["highlight"]],
        x="scan",
        y="non_linearity_score",
        color_discrete_sequence=["red"],
        hover_data=["device", "scan", "non_linearity_score"],
    ).data[0]
)

# Update layout for better readability
fig.update_layout(legend_title_text="Device")
fig.update_traces(marker=dict(size=8))

# Show the plot
fig.show()

fig.write_html("pid_nonlinearity.html")


# Process Name
# Analyze process name patterns
def extract_prefix(name):
    return name.split(".")[0] if "." in name else name


process_prefixes = df["procName"].apply(extract_prefix)
prefix_counts = process_prefixes.value_counts()

print("\nTop 10 process name prefixes:")
print(prefix_counts.head(10))

# Process Persistence
process_persistence = df.groupby("procName")["scan"].nunique() / df["scan"].nunique()

persistent_processes = process_persistence[process_persistence > 0.95]
print("\nProcesses present in over 95% of scans:")
print(persistent_processes.head(10))

# Convert to DataFrame for Plotly Express
persistent_processes_df = persistent_processes.reset_index()
persistent_processes_df.columns = ["ProcessName", "Persistence"]

# Create the bar chart using Plotly Express
fig = px.bar(
    persistent_processes_df,
    x="ProcessName",
    y="Persistence",
    title="Processes Present in Over 95% of Scans",
    labels={"ProcessName": "Process Name", "Persistence": "Persistence"},
    text="Persistence",
)

# Display the bar chart
fig.show()

fig.write_html("persistent_processes.html")

# ### Anomaly Detection
# 1. String Similarity in Process Names: Detect process names that are similar to benign processes but have slight deviations.


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


# Example to find similar process names
def find_similar_processes(data):
    process_names = data["procName"].unique()
    similar_process_pairs = []

    for i, name1 in enumerate(process_names):
        for name2 in process_names[i + 1 :]:
            if name1 != name2 and similar(name1, name2) > 0.8:
                similar_process_pairs.append((name1, name2))

    return similar_process_pairs


similar_processes = find_similar_processes(df)
print("Similar Process Pairs:", similar_processes)

# Extract unique process names
proc_names = df["procName"].unique()

# Load a pre-trained sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embeddings for process names
embeddings = model.encode(proc_names)

# Normalize the embeddings
scaler = StandardScaler()
normalized_embeddings = scaler.fit_transform(embeddings)

# Perform clustering using HDBSCAN
clusterer = HDBSCAN(min_cluster_size=30, min_samples=1)
cluster_labels = clusterer.fit_predict(normalized_embeddings)

# Create a DataFrame with results
results = pd.DataFrame(
    {
        "procName": proc_names,
        "cluster": cluster_labels,
        "outlier_score": clusterer.outlier_scores_,
    }
)

# Sort by outlier score in descending order
results = results.sort_values("outlier_score", ascending=False)

# Identify outliers (you can adjust the threshold as needed)
outlier_threshold = results["outlier_score"].mean() + 2 * results["outlier_score"].std()
outliers = results[results["outlier_score"] > outlier_threshold]

# Apply UMAP for dimensionality reduction
umap = UMAP(n_neighbors=20, n_components=2, min_dist=0.1, metric="cosine")
umap_embeddings = umap.fit_transform(normalized_embeddings)
# Convert proc_names to a list for indexing
proc_names_list = proc_names.tolist()

# Create a DataFrame for the embeddings
df_embeddings = pd.DataFrame(umap_embeddings, columns=["UMAP_1", "UMAP_2"])
df_embeddings["procName"] = proc_names_list
df_embeddings["cluster"] = cluster_labels

# Mark outliers in the DataFrame
df_embeddings["outlier"] = df_embeddings["procName"].isin(outliers["procName"])
df_embeddings["outlier_score"] = df_embeddings.apply(
    lambda row: (
        outliers[outliers["procName"] == row["procName"]]["outlier_score"].values[0]
        if row["procName"] in outliers["procName"].values
        else None
    ),
    axis=1,
)

# Create the interactive plot
fig = px.scatter(
    df_embeddings,
    x="UMAP_1",
    y="UMAP_2",
    color="cluster",
    hover_data=["procName", "outlier_score"],
    title="Process Name Clustering with Outliers Highlighted",
    labels={"UMAP_1": "UMAP Dimension 1", "UMAP_2": "UMAP Dimension 2"},
    opacity=0.7,
)

# Highlight outliers
outliers_data = df_embeddings[df_embeddings["outlier"]]
fig.add_scatter(
    x=outliers_data["UMAP_1"],
    y=outliers_data["UMAP_2"],
    mode="markers",
    marker=dict(color="red", size=10, line=dict(width=2, color="DarkSlateGrey")),
    name="Outliers",
    text=outliers_data["procName"],
)

# Update layout
fig.update_layout(
    legend=dict(title="Clusters"),
    xaxis_title="UMAP Dimension 1",
    yaxis_title="UMAP Dimension 2",
)

# Show the plot
fig.show()

#
fig.write_html("procName_outliers.html")

# ## Future Work
# ### PID resets

from scipy.stats import zscore


# Function to detect PID resets
def detect_pid_resets(pids):
    return np.where(np.diff(pids) < 0)[0] + 1


# Function to calculate PID growth rate
def pid_growth_rate(pids, timestamps):
    return np.diff(pids) / np.diff(timestamps.astype(int) / 1e9)


# Detect PID resets
reset_indices = detect_pid_resets(df["pid"].values)
reset_timestamps = df["readableTimestamp"].iloc[reset_indices]

# Calculate PID growth rate
growth_rate = pid_growth_rate(df["pid"].values, df["readableTimestamp"].values)


# Calculate z-score of growth rate
growth_rate_zscore = zscore(growth_rate)

# Identify anomalies (excluding reset points)
anomaly_threshold = 3  # z-score threshold for anomalies
anomalies = np.abs(growth_rate_zscore) > anomaly_threshold
anomalies = np.insert(anomalies, 0, False)  # Align with original dataframe

# Remove anomalies at reset points
for idx in reset_indices:
    if idx > 0:
        anomalies[idx - 1 : idx + 1] = False

# Analyze anomalies
anomaly_df = df[anomalies].copy()
anomaly_df["growth_rate"] = np.insert(growth_rate, 0, 0)[anomalies]
anomaly_df["growth_rate_zscore"] = np.insert(growth_rate_zscore, 0, 0)[anomalies]

print("Top 10 PID anomalies (excluding resets):")
print(
    anomaly_df.sort_values("growth_rate_zscore", key=abs, ascending=False)[
        ["readableTimestamp", "pid", "procName", "growth_rate", "growth_rate_zscore"]
    ].head(10)
)

# Calculate statistics
total_processes = len(df)
total_anomalies = anomalies.sum()
anomaly_percentage = (total_anomalies / total_processes) * 100

print(f"\nTotal processes analyzed: {total_processes}")
print(f"Number of PID resets detected: {len(reset_timestamps)}")
print(f"Number of anomalies detected: {total_anomalies}")
print(f"Percentage of processes flagged as anomalous: {anomaly_percentage:.2f}%")

# Analyze processes around reset points
reset_window = 5  # Number of processes to check before and after reset
processes_around_resets = []

for idx in reset_indices:
    start = max(0, idx - reset_window)
    end = min(len(df), idx + reset_window)
    processes_around_resets.extend(df["procName"].iloc[start:end].tolist())

print("\nTop 10 processes observed around PID resets:")
print(pd.Series(processes_around_resets).value_counts().head(10))

# Anomalies

from pyod.models.knn import KNN
from pyod.models.iforest import IForest
from pyod.models.lof import LOF
from sklearn.preprocessing import StandardScaler

# Prepare the data for anomaly detection
# We'll use PID and readableTimestamp as features

outliers_df = pd.read_csv("pseudoProcess.csv")
outliers_df["readableTimestamp"] = pd.to_datetime(outliers_df["readableTimestamp"])
# Remove date before 2024
outliers_df = outliers_df[outliers_df["readableTimestamp"].dt.year >= 2024]

# Handle missing or incorrect data (here we drop missing)
outliers_df = outliers_df.dropna()


# df['readableTimestamp'] = pd.to_numeric(df['readableTimestamp'])
# Prepare the data for anomaly detection
# We'll use PID and timestamp as features
X = outliers_df[["pid", "timestamp"]].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Initialize and fit the anomaly detection models
knn = KNN()
iforest = IForest(random_state=42)
lof = LOF()

knn.fit(X_scaled)
iforest.fit(X_scaled)
lof.fit(X_scaled)

# Get the anomaly scores
knn_scores = knn.decision_function(X_scaled)
iforest_scores = iforest.decision_function(X_scaled)
lof_scores = lof.decision_function(X_scaled)

# Add the anomaly scores to the dataframe
outliers_df["knn_score"] = knn_scores
outliers_df["iforest_score"] = iforest_scores
outliers_df["lof_score"] = lof_scores


# Function to get top anomalies
def get_top_anomalies(df, score_column, n=10):
    return df.nlargest(n, score_column)


# Get top anomalies for each method
top_knn = get_top_anomalies(outliers_df, "knn_score")
top_iforest = get_top_anomalies(outliers_df, "iforest_score")
top_lof = get_top_anomalies(outliers_df, "lof_score")

# Print top anomalies
print("Top KNN Anomalies:")
print(top_knn[["readableTimestamp", "pid", "procName", "knn_score"]])

print("\nTop Isolation Forest Anomalies:")
print(top_iforest[["readableTimestamp", "pid", "procName", "iforest_score"]])

print("\nTop LOF Anomalies:")
print(top_lof[["readableTimestamp", "pid", "procName", "lof_score"]])


### NEED MORE WORK

# # Define a function to plot anomalies
# def plot_anomalies(data, score_column, title, color_label):
#     plt.figure(figsize=(12, 8))
#     plt.scatter(data['readableTimestamp'], data['pid'], c=data[score_column], cmap='viridis')
#     plt.colorbar(label=color_label)
#     plt.title(title)
#     plt.xlabel('Timestamp')
#     plt.ylabel('PID')
#     plt.show()
#     # Uncomment the following lines to save the plots as images
#     # plt.savefig(f'{score_column}_anomalies.png')
#     # plt.close()

# # Plot KNN anomalies
# plot_anomalies(outliers_df, 'knn_score', 'Process Anomalies (KNN)', 'Anomaly Score (KNN)')

# # Plot Isolation Forest anomalies
# plot_anomalies(outliers_df, 'iforest_score', 'Process Anomalies (Isolation Forest)', 'Anomaly Score (Isolation Forest)')

# # Plot LOF anomalies
# plot_anomalies(outliers_df, 'lof_score', 'Process Anomalies (LOF)', 'Anomaly Score (LOF)')


# Analyze agreement between methods
def get_top_n_indices(scores, n=10):
    return set(scores.argsort()[-n:])


top_knn_indices = get_top_n_indices(knn_scores)
top_iforest_indices = get_top_n_indices(iforest_scores)
top_lof_indices = get_top_n_indices(lof_scores)

agreement = top_knn_indices & top_iforest_indices & top_lof_indices

print("\nAnomalies detected by all three methods:")
print(outliers_df.iloc[list(agreement)][["readableTimestamp", "pid", "procName"]])

# Analyze anomalies by process name
process_anomaly_counts = (
    outliers_df.groupby("procName")
    .agg({"knn_score": "mean", "iforest_score": "mean", "lof_score": "mean"})
    .sort_values("knn_score", ascending=False)
)

print("\nTop potentially anomalous processes (by average KNN score):")
print(process_anomaly_counts.head(10))
