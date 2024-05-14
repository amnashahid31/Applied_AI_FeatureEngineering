# -*- coding: utf-8 -*-
"""Feature_Engineering.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/18Pv5Rc-0xRt5bWdcYWeGeNuh_DQ8ZuBe
"""

# For mounting the drive to google colab
from google.colab import drive
drive.mount('/content/drive')

# Libraries
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor

# Order data file's header definition
order_data_header = [
    "Order_ID",
    "Driver_ID",
    "Passenger_ID",
    "Start_Region_Hash",
    "Destination_Region_Hash",
    "Price",
    "Time"
]

# Cluster map file's header definition
cluster_map_header = ["Region_Hash", "Region_ID"]

# Data loading
cluster_map = pd.read_table(
    "/content/drive/My Drive/AI_assignment_3/training_data/cluster_map/cluster_map",
    sep='\t',
    names=cluster_map_header,
    header=None
)

# Path for order files
order_data_folder = '/content/drive/My Drive/AI_assignment_3/training_data/order_data/'

# Files having same pattern of date.
order_data_files = [f for f in os.listdir(order_data_folder) if f.startswith("order_data_")]

# Order data files are loaded here
order_data = pd.concat(
    [pd.read_table(os.path.join(order_data_folder, f), sep='\t', names=order_data_header, header=None)
     for f in order_data_files],
    ignore_index=True
)

# Obtaining Region IDs by merging cluster data and order data files
order_data = order_data.merge(
    cluster_map,
    left_on='Start_Region_Hash',
    right_on='Region_Hash'
)

# conversion of time to datetime
order_data['Time'] = pd.to_datetime(order_data['Time'])

# Define a function to convert datetime to a time slot
def get_time_slot(dt):
    # Define start time
    base_time = datetime(dt.year, dt.month, dt.day, 0, 0)
    # Calculate slot
    slot_number = int((dt - base_time).total_seconds() / 600) + 1
    # Label the slot
    return f"{dt.strftime('%Y-%m-%d')}-{slot_number}"

# Column for time slots
order_data['time_slot'] = order_data['Time'].apply(get_time_slot)

# Calculating demand (total number of orders in each region and time slot)
demand = order_data.groupby(['Region_ID', 'time_slot']).size().reset_index(name='demand')

# Calculating supply (total number of fulfilled orders in each region and time slot)
supply = order_data[order_data['Driver_ID'].notnull()].groupby(['Region_ID', 'time_slot']).size().reset_index(name='supply')

# Combining demand and supply for calculating the gap
gap_data = demand.merge(supply, on=['Region_ID', 'time_slot'], how='left').fillna(0)
gap_data['gap'] = gap_data['demand'] - gap_data['supply']


# Spliting the 'time_slot' into 'day' and 'slot' number
gap_data['day'] = gap_data['time_slot'].apply(lambda x: x.split("-")[0])
gap_data['slot'] = gap_data['time_slot'].apply(lambda x: int(x.split("-")[2]))

# Columns for the regression model
regression_data = gap_data[['Region_ID', 'day', 'slot', 'gap']]         #already selected in assignment

# Spliting data into training and testing sets
train_data, test_data = train_test_split(regression_data, test_size=0.2, random_state=42)

# Features and target for the model
X_train = train_data[['Region_ID', 'day', 'slot']]
y_train = train_data['gap']
X_test = test_data[['Region_ID', 'day', 'slot']]
y_test = test_data['gap']

# Initialize and train the linear regression model
regressor = LinearRegression()
regressor.fit(X_train, y_train)

# Predicting the gap for the test data
y_pred_lr = regressor.predict(X_test)

# Performance analysis of model
mae_lr = mean_absolute_error(y_test, y_pred_lr)
rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
r_squared_lr = r2_score(y_test, y_pred_lr)

print("Linear regression Mean Absolute Error:", mae_lr)
print("Linear regression Root Mean Squared Error:", rmse_lr)
print("Linear regression R-squared:", r_squared_lr)

# Initialize the kNN regressor with k=3
knn_regressor = KNeighborsRegressor(n_neighbors=3)
knn_regressor.fit(X_train, y_train)
y_pred_knn = knn_regressor.predict(X_test)
mae_knn = mean_absolute_error(y_test, y_pred_knn)
rmse_knn = np.sqrt(mean_squared_error(y_test, y_pred_knn))
r_squared_knn = r2_score(y_test, y_pred_knn)

print("\n")

print("kNN Mean Absolute Error:", mae_knn)
print("kNN Root Mean Squared Error:", rmse_knn)
print("kNN R-squared:", r_squared_knn)

# Initialize and fit the Decision Tree regression model
tree_regressor = DecisionTreeRegressor(random_state=42)
tree_regressor.fit(X_train, y_train)
y_pred_tree = tree_regressor.predict(X_test)
mae_tree = mean_absolute_error(y_test, y_pred_tree)
rmse_tree = np.sqrt(mean_squared_error(y_test, y_pred_tree))
r_squared_tree = r2_score(y_test, y_pred_tree)

print("\n")

print("Decision Tree Mean Absolute Error:", mae_tree)
print("Decision Tree Root Mean Squared Error:", rmse_tree)
print("Decision Tree R-squared:", r_squared_tree)
print("\n")

# Testing predictions by checking the regressor on specific values
new_data = pd.DataFrame({
    'Region_ID': [2],
    'day': [23],
    'slot': [2]
})

# Scaling the features using StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
new_data_scaled = scaler.transform(new_data)

# Predicting the gap by decision trees
predicted_gap_tree = tree_regressor.predict(new_data_scaled)

# Adding the gap valu in dataframe
new_data['predicted_gap'] = predicted_gap_tree

# Printing the results
print("Predicted gap for Region ID: 2, Day: 23, Slot: 2 using Decision Tree: \n")
print(new_data)
print("\n")


# Plot actual vs predicted values for all three models
plt.figure(figsize=(18, 6))

# Linear Regression
plt.subplot(1, 3, 1)
plt.scatter(y_test, y_pred_lr, color='blue', label='Actual vs Predicted (Linear Regression)')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2, label='Ideal')
plt.xlabel('Actual Values')
plt.ylabel('Predicted Values')
plt.title('Linear Regression')
plt.legend()
plt.grid(True)

# kNN Regression
plt.subplot(1, 3, 2)
plt.scatter(y_test, y_pred_knn, color='green', label='Actual vs Predicted (kNN Regression)')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2, label='Ideal')
plt.xlabel('Actual Values')
plt.ylabel('Predicted Values')
plt.title('kNN Regression')
plt.legend()
plt.grid(True)

# Decision Tree Regression
plt.subplot(1, 3, 3)
plt.scatter(y_test, y_pred_tree, color='orange', label='Actual vs Predicted (Decision Tree Regression)')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2, label='Ideal')
plt.xlabel('Actual Values')
plt.ylabel('Predicted Values')
plt.title('Decision Tree Regression')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()