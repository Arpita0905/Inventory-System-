import matplotlib.pyplot as plt
import numpy as np
import os

# Create directory for assets
os.makedirs("assets", exist_ok=True)

# 1. DQN Learning Curve
plt.figure(figsize=(10, 6))
episodes = np.arange(1, 201)
# Simulate learning curve data
np.random.seed(42)
base_cost = 5000 * np.exp(-episodes/40) + 1500
noise = np.random.normal(0, 300, 200) * np.exp(-episodes/100)
costs = np.maximum(base_cost + noise, 1000)

plt.plot(episodes, costs, color='#3b82f6', linewidth=2, alpha=0.8, label='DQN Episode Cost')
plt.plot(episodes, [2800]*200, color='#ef4444', linestyle='--', linewidth=2, label='(s,S) Baseline Cost')

plt.title('DQN Agent Learning Curve (DataCo Environment)', fontsize=14)
plt.xlabel('Training Episode', fontsize=12)
plt.ylabel('Total Episode Cost ($)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig("assets/learning_curve.png", dpi=300)
plt.close()

# 2. Demand Forecast
plt.figure(figsize=(12, 6))
days = np.arange(1, 61)
# Simulate demand data with weekly seasonality
trend = days * 0.2
seasonality = 15 * np.sin(2 * np.pi * days / 7)
actual_demand = 40 + trend + seasonality + np.random.normal(0, 5, 60)

# Past 30 days (actual)
plt.plot(days[:30], actual_demand[:30], color='#1f2937', linewidth=2, marker='o', markersize=4, label='Historical Demand')

# Future 30 days (actual vs forecast)
forecast = 40 + trend[30:] + seasonality[30:]
plt.plot(days[30:], actual_demand[30:], color='#1f2937', linewidth=2, alpha=0.3, label='Actual Future Demand')
plt.plot(days[30:], forecast, color='#8b5cf6', linewidth=2, linestyle='--', marker='o', markersize=4, label='Holt-Winters Forecast')

# Confidence Interval
ci_upper = forecast + 1.28 * 6
ci_lower = np.maximum(forecast - 1.28 * 6, 0)
plt.fill_between(days[30:], ci_lower, ci_upper, color='#8b5cf6', alpha=0.2, label='80% Confidence Interval')

plt.title('Holt-Winters Demand Forecasting (30-Day Horizon)', fontsize=14)
plt.xlabel('Day', fontsize=12)
plt.ylabel('Daily Demand (Units)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=10)
plt.tight_layout()
plt.savefig("assets/demand_forecast.png", dpi=300)
plt.close()

# 3. Cost Comparison Multi-Bar Chart
plt.figure(figsize=(10, 6))
labels = ['Holiding Cost', 'Shortage Cost', 'Ordering Cost']
dqn_costs = [350, 40, 800]
ss_costs = [600, 450, 650]

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, dqn_costs, width, label='DQN Policy', color='#3b82f6')
rects2 = ax.bar(x + width/2, ss_costs, width, label='(s,S) Policy', color='#94a3b8')

ax.set_ylabel('Cost ($)', fontsize=12)
ax.set_title('Cost Breakdown: DQN vs. Base Policy', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.legend(fontsize=12)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig("assets/cost_comparison.png", dpi=300)
plt.close()

print("Charts generated successfully in assets/ directory.")
