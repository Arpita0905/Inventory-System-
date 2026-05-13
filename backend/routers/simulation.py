"""Scenario simulation router — run what-if analyses with the trained RL agent."""
from fastapi import APIRouter, HTTPException
from schemas import ScenarioRequest, ScenarioResponse
from scenario_engine import run_scenario, ScenarioConfig

router = APIRouter(prefix="/api", tags=["Scenario Simulation"])


@router.post("/simulate-scenario", response_model=ScenarioResponse)
def simulate_scenario(req: ScenarioRequest):
    """
    Run a what-if simulation using the trained DQN agent under
    modified demand, lead-time, and cost conditions.

    The agent is NOT retrained — it uses the saved policy weights
    and evaluates them against the modified environment.
    """
    try:
        config = ScenarioConfig(
            demand_multiplier=req.demand_multiplier,
            lead_time_multiplier=req.lead_time_multiplier,
            holding_cost_multiplier=req.holding_cost_multiplier,
            stockout_cost_multiplier=req.stockout_cost_multiplier,
            simulation_days=req.simulation_days,
        )

        result = run_scenario(config)

        return ScenarioResponse(
            total_cost=result.total_cost,
            stockouts=result.stockouts,
            service_level=result.service_level,
            average_inventory=result.average_inventory,
            recommendation=result.recommendation,
            daily_breakdown=result.daily_breakdown,
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(e)}",
        )
