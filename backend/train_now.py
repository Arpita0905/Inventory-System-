"""Train with more episodes for higher service level."""
from ai_models.rl_agent.trainer import train_agent

print("Training DQN agent (1000 episodes for better convergence)...")
print("This may take 1-2 minutes...\n")

results = train_agent(episodes=1000)

print(f"Training complete!")
print(f"  Service Level:  {results['service_level']}%")
print(f"  RL Avg Cost:    ${results['rl_avg_cost_last50']}")
print(f"  Baseline Cost:  ${results['baseline_avg_cost']}")
print(f"  Cost Reduction: {results['cost_reduction_pct']}%")
