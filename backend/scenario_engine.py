"""
Scenario-Based Simulation Engine
=================================
Runs the trained DQN agent under user-defined "what-if" conditions
(demand surges, supplier delays, cost changes) WITHOUT retraining.
Produces KPIs and a natural-language recommendation.
"""

import os
import json
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any

from ai_models.rl_agent.inventory_env import InventoryEnv
from ai_models.rl_agent.dqn_agent import DQNAgent

# Path to the saved DQN model weights
MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ai_models", "saved_models",
)
MODEL_PATH = os.path.join(MODELS_DIR, "dqn_weights.json")
PARAMS_PATH = os.path.join(MODELS_DIR, "env_params.json")


def _load_env_params():
    """Load environment params saved during training, or use DataCo-derived defaults."""
    if os.path.exists(PARAMS_PATH):
        with open(PARAMS_PATH) as f:
            params = json.load(f)
            print(f"[INFO] Loaded env params from training: demand={params.get('mean_demand')}")
            return params
    # Fallback: DataCo-realistic defaults
    return {
        "max_stock": 1200,
        "max_order": 600,
        "num_actions": 25,
        "holding_cost": 2.5,
        "shortage_cost": 14.0,
        "ordering_cost": 80.0,
        "mean_demand": 46.0,
        "demand_std": 25.0,
        "lead_time_mean": 4.0,
        "lead_time_std": 1.5,
    }


# Load once at module level
DEFAULT_PARAMS = _load_env_params()


@dataclass
class ScenarioConfig:
    """User-supplied scenario multipliers and duration."""
    demand_multiplier: float = 1.0
    lead_time_multiplier: float = 1.0
    holding_cost_multiplier: float = 1.0
    stockout_cost_multiplier: float = 1.0
    simulation_days: int = 60


@dataclass
class ScenarioResult:
    """Aggregated simulation output."""
    total_cost: float = 0.0
    stockouts: int = 0
    service_level: float = 0.0
    average_inventory: float = 0.0
    recommendation: str = ""
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


def run_scenario(config: ScenarioConfig) -> ScenarioResult:
    """
    Execute the trained DQN policy under modified environment conditions.

    1. Apply multipliers to the base environment parameters.
    2. Load saved DQN weights (no retraining — pure exploitation).
    3. Simulate for `simulation_days` steps.
    4. Aggregate KPIs and generate a recommendation.
    """

    # --- 1. Build modified environment ---
    env = InventoryEnv(
        max_stock=DEFAULT_PARAMS["max_stock"],
        max_order=DEFAULT_PARAMS["max_order"],
        num_actions=DEFAULT_PARAMS["num_actions"],
        holding_cost=DEFAULT_PARAMS["holding_cost"] * config.holding_cost_multiplier,
        shortage_cost=DEFAULT_PARAMS["shortage_cost"] * config.stockout_cost_multiplier,
        ordering_cost=DEFAULT_PARAMS["ordering_cost"],
        mean_demand=DEFAULT_PARAMS["mean_demand"] * config.demand_multiplier,
        demand_std=DEFAULT_PARAMS["demand_std"] * config.demand_multiplier,
        lead_time_mean=DEFAULT_PARAMS["lead_time_mean"] * config.lead_time_multiplier,
        lead_time_std=DEFAULT_PARAMS["lead_time_std"] * config.lead_time_multiplier,
        max_steps=config.simulation_days,
    )

    # --- 2. Load trained agent (exploitation only) ---
    agent = DQNAgent(state_dim=env.state_dim, action_dim=env.action_dim)

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "No trained model found. Please train the RL agent first "
            "via POST /api/rl/train before running simulations."
        )

    agent.load(MODEL_PATH)
    agent.epsilon = 0.0  # Pure exploitation — no exploration

    # --- 3. Run simulation ---
    state = env.reset()
    for _ in range(config.simulation_days):
        action = agent.select_action(state)
        state, _, done, _ = env.step(action)
        if done:
            break

    # --- 4. Aggregate KPIs ---
    history = env.history
    total_cost = round(sum(h["total_cost"] for h in history), 2)
    total_stockouts = sum(1 for h in history if h["shortage"] > 0)
    total_demand = sum(h["demand"] for h in history)
    total_fulfilled = sum(h["fulfilled"] for h in history)
    service_level = round(
        (total_fulfilled / max(total_demand, 1)) * 100, 1
    )
    average_inventory = round(
        np.mean([h["stock_after"] for h in history]), 1
    )

    # Build per-day breakdown for frontend charts
    daily_breakdown = [
        {
            "day": h["step"] + 1,
            "stock": h["stock_after"],
            "demand": h["demand"],
            "fulfilled": h["fulfilled"],
            "shortage": h["shortage"],
            "order_placed": h["order_placed"],
            "holding_cost": h["holding_cost"],
            "shortage_cost": h["shortage_cost"],
            "ordering_cost": h["ordering_cost"],
            "total_cost": h["total_cost"],
        }
        for h in history
    ]

    # --- 5. Generate recommendation ---
    recommendation = _generate_recommendation(
        config=config,
        total_cost=total_cost,
        total_stockouts=total_stockouts,
        service_level=service_level,
        average_inventory=average_inventory,
        history=history,
    )

    return ScenarioResult(
        total_cost=total_cost,
        stockouts=total_stockouts,
        service_level=service_level,
        average_inventory=average_inventory,
        recommendation=recommendation,
        daily_breakdown=daily_breakdown,
    )


def _generate_recommendation(
    config: ScenarioConfig,
    total_cost: float,
    total_stockouts: int,
    service_level: float,
    average_inventory: float,
    history: list,
) -> str:
    """
    Rule-based reasoning engine that analyzes simulation results
    and produces actionable, human-readable recommendations.
    """
    insights = []
    actions = []

    # --- Analyze demand impact ---
    if config.demand_multiplier > 1.15:
        pct = round((config.demand_multiplier - 1) * 100)
        insights.append(
            f"Demand was increased by {pct}%, simulating a surge scenario."
        )
        if total_stockouts > 3:
            actions.append(
                "Increase reorder point and safety stock to buffer against "
                "higher demand. Consider raising maximum order quantities."
            )
    elif config.demand_multiplier < 0.85:
        pct = round((1 - config.demand_multiplier) * 100)
        insights.append(
            f"Demand was reduced by {pct}%, simulating a slowdown."
        )
        if average_inventory > 100:
            actions.append(
                "Reduce reorder point to avoid excess holding costs. "
                "Consider smaller, more frequent orders."
            )

    # --- Analyze lead time impact ---
    if config.lead_time_multiplier > 1.2:
        pct = round((config.lead_time_multiplier - 1) * 100)
        insights.append(
            f"Supplier lead time was extended by {pct}%, indicating potential delays."
        )
        actions.append(
            "Increase safety stock levels to compensate for longer lead times. "
            "Evaluate alternative suppliers with shorter delivery windows."
        )

    # --- Analyze cost structure ---
    total_holding = sum(h["holding_cost"] for h in history)
    total_shortage = sum(h["shortage_cost"] for h in history)

    if total_shortage > total_holding * 2:
        actions.append(
            "Shortage costs dominate — prioritize stock availability over "
            "minimizing holding costs. Raise the reorder trigger level."
        )
    elif total_holding > total_shortage * 3 and total_stockouts == 0:
        actions.append(
            "Holding costs are disproportionately high with zero stockouts. "
            "You can safely lower safety stock to reduce carrying expenses."
        )

    # --- Analyze service level ---
    if service_level >= 98:
        insights.append(
            f"Service level is excellent at {service_level}% — nearly all demand was fulfilled."
        )
    elif service_level >= 90:
        insights.append(
            f"Service level is good at {service_level}%, but there is room for improvement."
        )
    else:
        insights.append(
            f"Service level dropped to {service_level}% — significant demand was unmet."
        )
        actions.append(
            "Urgently increase inventory buffers. The current policy cannot "
            "sustain this scenario without major stockouts."
        )

    # --- Stockout severity ---
    if total_stockouts == 0:
        insights.append("No stockout events occurred during the simulation.")
    elif total_stockouts <= 5:
        insights.append(
            f"{total_stockouts} stockout events occurred — minor but worth monitoring."
        )
    else:
        insights.append(
            f"{total_stockouts} stockout events occurred — this is a critical concern."
        )

    # --- Default fallback ---
    if not actions:
        actions.append(
            "The current RL policy handles this scenario well. "
            "No immediate changes are recommended."
        )

    # Build final recommendation string
    analysis = " ".join(insights)
    advice = " ".join(actions)
    return f"📊 Analysis: {analysis}\n\n💡 Recommendation: {advice}"
