"""RL training runner – trains DQN agent using REAL data from the database."""
import os
import sys
import json
import numpy as np

# Ensure backend root is on the path so database/models can be imported
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from ai_models.rl_agent.inventory_env import InventoryEnv, BaselineSsPolicy
from ai_models.rl_agent.dqn_agent import DQNAgent

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saved_models")
RESULTS_PATH = os.path.join(MODELS_DIR, "rl_results.json")
MODEL_PATH = os.path.join(MODELS_DIR, "dqn_weights.json")


def _get_real_demand_stats():
    """
    Query the database for real DataCo demand statistics.
    Returns a dict with mean_demand, demand_std, holding_cost, shortage_cost,
    ordering_cost, lead_time_mean computed from the actual data.
    Falls back to reasonable defaults if DB is unavailable.
    """
    try:
        from database import SessionLocal
        from models import Product, DemandHistory, Order, OrderStatus
        db = SessionLocal()

        products = db.query(Product).all()
        if not products:
            db.close()
            raise ValueError("No products in database")

        all_means = []
        all_stds = []
        all_holding = []
        all_shortage = []
        all_ordering = []

        for p in products:
            demands = db.query(DemandHistory).filter(
                DemandHistory.product_id == p.id
            ).all()
            qtys = [d.quantity for d in demands]
            if qtys:
                all_means.append(float(np.mean(qtys)))
                all_stds.append(float(np.std(qtys)))
            all_holding.append(float(p.holding_cost_per_unit))
            all_shortage.append(float(p.shortage_cost_per_unit))
            all_ordering.append(float(p.ordering_cost))

        # Get average lead time from delivered orders
        delivered = db.query(Order).filter(
            Order.status == OrderStatus.delivered
        ).all()
        lead_times = [o.lead_time_days for o in delivered if o.lead_time_days]
        avg_lead_time = float(np.mean(lead_times)) if lead_times else 4.0

        db.close()

        mean_demand = float(np.mean(all_means)) if all_means else 46.0
        demand_std = float(np.mean(all_stds)) if all_stds else 25.0

        stats = {
            "mean_demand": round(mean_demand, 1),
            "demand_std": round(demand_std, 1),
            "holding_cost": round(float(np.mean(all_holding)), 2),
            "shortage_cost": round(float(np.mean(all_shortage)), 2),
            "ordering_cost": round(float(np.mean(all_ordering)), 2),
            "lead_time_mean": round(avg_lead_time, 1),
            "lead_time_std": 1.5,
            "num_products": len(products),
        }
        print(f"📊 Real data stats: demand={stats['mean_demand']}±{stats['demand_std']}, "
              f"lead_time={stats['lead_time_mean']}d, "
              f"costs: hold={stats['holding_cost']}, short={stats['shortage_cost']}, "
              f"order={stats['ordering_cost']}")
        return stats

    except Exception as e:
        print(f"⚠️  Could not load DB stats ({e}), using DataCo-derived defaults")
        return {
            "mean_demand": 46.0,
            "demand_std": 25.0,
            "holding_cost": 2.5,
            "shortage_cost": 14.0,
            "ordering_cost": 80.0,
            "lead_time_mean": 4.0,
            "lead_time_std": 1.5,
            "num_products": 20,
        }


def train_agent(episodes=800, max_steps=90, product_params=None):
    """
    Train the DQN agent using real DataCo demand data.
    Optimized for high service levels (85%+).

    Returns training results dict.
    """
    # Pull real stats from the database
    real_stats = _get_real_demand_stats()

    # Merge with any user-supplied overrides
    params = {**real_stats, **(product_params or {})}
    mean_demand = params["mean_demand"]
    demand_std = params["demand_std"]

    # Scale max_stock and max_order to the real demand levels
    # Need enough capacity for ~2x peak demand * lead_time
    max_stock = max(1000, int(mean_demand * params["lead_time_mean"] * 6))
    max_order = max(400, int(mean_demand * params["lead_time_mean"] * 3))

    print(f"🏗️  Environment: max_stock={max_stock}, max_order={max_order}, "
          f"demand={mean_demand}±{demand_std}")

    env = InventoryEnv(
        max_stock=max_stock,
        max_order=max_order,
        num_actions=25,  # finer-grained actions for better control
        holding_cost=params["holding_cost"],
        shortage_cost=params["shortage_cost"],
        ordering_cost=params["ordering_cost"],
        mean_demand=mean_demand,
        demand_std=demand_std,
        lead_time_mean=params["lead_time_mean"],
        lead_time_std=params.get("lead_time_std", 1.5),
        max_steps=max_steps,
    )

    agent = DQNAgent(
        state_dim=env.state_dim,
        action_dim=env.action_dim,
        lr=0.0003,
        gamma=0.97,
        epsilon=1.0,
        epsilon_min=0.01,
        epsilon_decay=0.995,
        batch_size=128,
        memory_size=20000,
    )

    # Smart baseline (s,S) using real data parameters
    baseline_s = max(50, int(mean_demand * params["lead_time_mean"] * 1.5))
    baseline_S = max(200, int(mean_demand * params["lead_time_mean"] * 4))
    baseline = BaselineSsPolicy(
        s=baseline_s, S=baseline_S,
        num_actions=env.num_actions, max_order=env.max_order
    )

    rl_episode_costs = []
    rl_episode_rewards = []
    baseline_costs = []
    learning_curve = []
    best_service = 0
    best_cost = float('inf')
    best_weights = None

    print(f"🚀 Training DQN agent for {episodes} episodes...")

    # Train RL agent
    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        losses = []

        for _ in range(max_steps):
            action = agent.select_action(state)
            next_state, reward, done, info = env.step(action)
            agent.store(state, action, reward, next_state, done)
            loss = agent.train_step()
            if loss > 0:
                losses.append(loss)
            total_reward += reward
            state = next_state
            if done:
                break

        rl_episode_costs.append(round(env.total_cost, 2))
        rl_episode_rewards.append(round(total_reward, 2))
        avg_loss = round(float(np.mean(losses)), 4) if losses else 0

        # Calculate service level for this episode
        ep_service = env.total_fulfilled / max(env.total_demand, 1) * 100

        # Save best model — prioritize service level, then cost
        if episode >= 50:
            recent_costs = rl_episode_costs[-20:]
            recent_avg = np.mean(recent_costs)
            # Prefer models with high service level AND low cost
            if ep_service >= best_service - 2 and recent_avg < best_cost:
                best_cost = recent_avg
                best_service = ep_service
                best_weights = {
                    "W1": agent.W1.copy(), "b1": agent.b1.copy(),
                    "W2": agent.W2.copy(), "b2": agent.b2.copy(),
                    "W3": agent.W3.copy(), "b3": agent.b3.copy(),
                }

        # Progress logging every 100 episodes
        if (episode + 1) % 100 == 0:
            recent_sl = []
            old_eps = agent.epsilon
            agent.epsilon = 0.0
            for _ in range(5):
                s = env.reset()
                for _ in range(max_steps):
                    a = agent.select_action(s)
                    s, _, d, _ = env.step(a)
                    if d:
                        break
                recent_sl.append(env.total_fulfilled / max(env.total_demand, 1) * 100)
            agent.epsilon = old_eps
            avg_sl = np.mean(recent_sl)
            print(f"   Episode {episode+1}/{episodes}: "
                  f"cost={np.mean(rl_episode_costs[-50:]):.0f}, "
                  f"service={avg_sl:.1f}%, eps={agent.epsilon:.3f}")

        # Record every 5th episode for learning curve
        if (episode + 1) % 5 == 0 or episode == 0:
            learning_curve.append({
                "episode": episode + 1,
                "total_cost": round(env.total_cost, 2),
                "reward": round(total_reward, 2),
                "epsilon": round(agent.epsilon, 4),
                "avg_loss": avg_loss,
                "service_level": round(ep_service, 1),
            })

    # Restore best weights
    if best_weights:
        agent.W1 = best_weights["W1"]
        agent.b1 = best_weights["b1"]
        agent.W2 = best_weights["W2"]
        agent.b2 = best_weights["b2"]
        agent.W3 = best_weights["W3"]
        agent.b3 = best_weights["b3"]
        print(f"✅ Restored best weights (service={best_service:.1f}%, cost={best_cost:.0f})")

    # Evaluate baseline over 100 episodes
    eval_episodes = min(100, episodes)
    for _ in range(eval_episodes):
        state = env.reset()
        for _ in range(max_steps):
            stock = int(state[0] * env.max_stock)
            action = baseline.select_action(stock)
            state, _, done, _ = env.step(action)
            if done:
                break
        baseline_costs.append(round(env.total_cost, 2))

    # Final evaluation with trained agent (no exploration)
    agent.epsilon = 0.0
    eval_costs = []
    eval_service_levels = []
    final_rl_history = None

    for i in range(20):  # more eval episodes for stable stats
        state = env.reset()
        for _ in range(max_steps):
            action = agent.select_action(state)
            state, _, done, _ = env.step(action)
            if done:
                break
        eval_costs.append(env.total_cost)
        sl = env.total_fulfilled / max(env.total_demand, 1) * 100
        eval_service_levels.append(sl)
        if i == 0:
            final_rl_history = env.history

    # Summary statistics
    rl_avg = round(float(np.mean(rl_episode_costs[-50:])), 2)
    baseline_avg = round(float(np.mean(baseline_costs)), 2)
    cost_reduction = round((baseline_avg - rl_avg) / baseline_avg * 100, 1) if baseline_avg > 0 else 0
    avg_service_level = round(float(np.mean(eval_service_levels)), 1)

    print(f"\n🎯 Final Results:")
    print(f"   Service Level: {avg_service_level}%")
    print(f"   RL Avg Cost:   ${rl_avg}")
    print(f"   Baseline Cost: ${baseline_avg}")
    print(f"   Cost Reduction: {cost_reduction}%")

    results = {
        "episodes_trained": episodes,
        "rl_avg_cost_last50": rl_avg,
        "baseline_avg_cost": baseline_avg,
        "cost_reduction_pct": cost_reduction,
        "learning_curve": learning_curve,
        "final_episode": final_rl_history,
        "rl_costs": rl_episode_costs,
        "baseline_costs": baseline_costs[:len(rl_episode_costs)],
        "service_level": avg_service_level,
        "data_source": "DataCo SMART SUPPLY CHAIN",
        "env_params": {
            "max_stock": max_stock,
            "max_order": max_order,
            "mean_demand": mean_demand,
            "demand_std": demand_std,
            "lead_time_mean": params["lead_time_mean"],
        },
    }

    # Save — convert numpy types for JSON compatibility
    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_convert(i) for i in obj]
        return obj

    results = _convert(results)

    os.makedirs(MODELS_DIR, exist_ok=True)
    agent.save(MODEL_PATH)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f)

    # Also save the env params so scenario_engine can use them
    params_path = os.path.join(MODELS_DIR, "env_params.json")
    with open(params_path, "w") as f:
        json.dump({
            "max_stock": max_stock,
            "max_order": max_order,
            "num_actions": 25,
            "holding_cost": params["holding_cost"],
            "shortage_cost": params["shortage_cost"],
            "ordering_cost": params["ordering_cost"],
            "mean_demand": mean_demand,
            "demand_std": demand_std,
            "lead_time_mean": params["lead_time_mean"],
            "lead_time_std": params.get("lead_time_std", 1.5),
        }, f, indent=2)

    return results


def get_saved_results():
    """Load saved training results."""
    if not os.path.exists(RESULTS_PATH):
        return None
    with open(RESULTS_PATH) as f:
        return json.load(f)


if __name__ == "__main__":
    print("Training DQN agent with real DataCo data...")
    results = train_agent(episodes=800)
    print(f"\n✅ Training complete!")
    print(f"   RL avg cost (last 50): ${results['rl_avg_cost_last50']}")
    print(f"   Baseline avg cost:     ${results['baseline_avg_cost']}")
    print(f"   Cost reduction:        {results['cost_reduction_pct']}%")
    print(f"   Service level:         {results['service_level']}%")
