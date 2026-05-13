"""Inventory simulation environment for RL agent training (Gym-style interface)."""
import numpy as np


class InventoryEnv:
    """
    Single-SKU inventory management environment.

    State: [current_stock, pending_orders, forecasted_demand_mean, lead_time, days_of_supply]
    Action: order_quantity (discrete: 0 to max_order in steps)
    Reward: negative total cost (holding + shortage + ordering) with shaping
    """

    def __init__(
        self,
        max_stock=500,
        max_order=200,
        num_actions=21,  # 0, 10, 20, ..., 200
        holding_cost=0.5,
        shortage_cost=2.0,
        ordering_cost=25.0,
        mean_demand=20,
        demand_std=5,
        lead_time_mean=3,
        lead_time_std=1,
        max_steps=60,
    ):
        self.max_stock = max_stock
        self.max_order = max_order
        self.num_actions = num_actions
        self.action_space_values = np.linspace(0, max_order, num_actions).astype(int)
        self.holding_cost = holding_cost
        self.shortage_cost = shortage_cost
        self.ordering_cost = ordering_cost
        self.mean_demand = mean_demand
        self.demand_std = demand_std
        self.lead_time_mean = lead_time_mean
        self.lead_time_std = lead_time_std
        self.max_steps = max_steps

        # State dimensions
        self.state_dim = 5
        self.action_dim = num_actions

        self.reset()

    def reset(self):
        """Reset environment to initial state."""
        # Start with healthy stock — enough for several days of demand
        self.stock = int(self.mean_demand * np.random.uniform(3, 8))
        self.stock = min(self.stock, self.max_stock)
        self.step_count = 0
        self.pending_orders = []  # list of (arrival_step, quantity)
        self.total_cost = 0
        self.total_demand = 0
        self.total_fulfilled = 0
        self.history = []
        return self._get_state()

    def _get_pending_qty(self):
        """Total quantity in pending orders."""
        return sum(q for (_, q) in self.pending_orders)

    def _get_state(self):
        """Get normalized state vector."""
        pending_qty = self._get_pending_qty()
        effective_stock = self.stock + pending_qty
        days_of_supply = effective_stock / max(self.mean_demand, 1)

        return np.array([
            self.stock / self.max_stock,
            pending_qty / self.max_stock,
            self.mean_demand / 100.0,
            self.lead_time_mean / 10.0,
            min(days_of_supply / 20.0, 1.0),  # capped ratio
        ], dtype=np.float32)

    def step(self, action_idx):
        """Execute one time step."""
        order_qty = self.action_space_values[action_idx]

        # Process arriving orders
        arrived = [q for (t, q) in self.pending_orders if t <= self.step_count]
        self.stock += sum(arrived)
        self.pending_orders = [(t, q) for (t, q) in self.pending_orders if t > self.step_count]

        # Cap stock at max
        self.stock = min(self.stock, self.max_stock)

        # Place new order (with stochastic lead time)
        if order_qty > 0:
            lead_time = max(1, int(np.random.normal(self.lead_time_mean, self.lead_time_std)))
            self.pending_orders.append((self.step_count + lead_time, order_qty))

        # Generate demand
        demand = max(0, int(np.random.normal(self.mean_demand, self.demand_std)))

        # Calculate costs
        ordering_cost = self.ordering_cost if order_qty > 0 else 0

        # Fulfill demand
        fulfilled = min(self.stock, demand)
        shortage = demand - fulfilled
        self.stock -= fulfilled
        self.stock = min(self.stock, self.max_stock)  # cap at max

        # Track fulfillment
        self.total_demand += demand
        self.total_fulfilled += fulfilled

        holding_cost = self.holding_cost * self.stock
        shortage_cost = self.shortage_cost * shortage

        total_step_cost = holding_cost + shortage_cost + ordering_cost
        self.total_cost += total_step_cost

        # Record history (ensure native Python types for JSON serialization)
        self.history.append({
            "step": int(self.step_count),
            "stock_before": int(self.stock + fulfilled),
            "demand": int(demand),
            "fulfilled": int(fulfilled),
            "shortage": int(shortage),
            "order_placed": int(order_qty),
            "holding_cost": round(float(holding_cost), 2),
            "shortage_cost": round(float(shortage_cost), 2),
            "ordering_cost": round(float(ordering_cost), 2),
            "total_cost": round(float(total_step_cost), 2),
            "stock_after": int(self.stock),
        })

        self.step_count += 1
        done = self.step_count >= self.max_steps

        # Shaped reward: STRONGLY incentivize meeting demand (service level focus)
        reward = -total_step_cost * 0.01  # scale down raw cost to avoid dominating

        # Very strong fulfillment bonus / shortage penalty
        if demand > 0:
            fill_rate = fulfilled / demand
            reward += fill_rate * 15.0   # up to +15 for full fill
            if fill_rate >= 1.0:
                reward += 5.0            # perfect fill bonus
        if shortage > 0:
            reward -= shortage * 8.0     # -8 per unit short (harsh)

        # Proactive stocking bonus: reward keeping buffer above lead_time * demand
        target_buffer = self.mean_demand * self.lead_time_mean
        if self.stock >= target_buffer:
            reward += 3.0  # good buffer bonus
        elif self.stock < target_buffer * 0.3:
            reward -= 5.0  # critically low stock penalty

        # Bonus for placing orders proactively when stock is getting low
        if order_qty > 0 and self.stock < target_buffer * 1.5:
            reward += 2.0  # proactive ordering bonus

        return self._get_state(), reward, done, {
            "total_cost": self.total_cost,
            "shortage": shortage,
        }


class BaselineSsPolicy:
    """
    Classic (s, S) inventory policy.
    When stock drops to or below `s`, order up to `S`.
    """

    def __init__(self, s=40, S=150, num_actions=21, max_order=200):
        self.s = s
        self.S = S
        self.action_values = np.linspace(0, max_order, num_actions).astype(int)

    def select_action(self, stock_level):
        if stock_level <= self.s:
            target_qty = self.S - stock_level
            # Find closest action
            diffs = np.abs(self.action_values - target_qty)
            return int(np.argmin(diffs))
        return 0  # don't order
