"""RL Optimization router – train agent and view results."""
import threading
from fastapi import APIRouter, HTTPException
from ai_models.rl_agent.trainer import train_agent, get_saved_results

router = APIRouter(prefix="/api/rl", tags=["RL Agent"])

# Track training state
_training_state = {"status": "idle", "progress": 0}


@router.post("/train")
def start_training(episodes: int = 800):
    """Start RL agent training with real DataCo data (runs in background)."""
    if _training_state["status"] == "training":
        raise HTTPException(status_code=409, detail="Training already in progress")

    _training_state["status"] = "training"
    _training_state["progress"] = 0

    def run():
        try:
            results = train_agent(episodes=episodes)
            _training_state["status"] = "complete"
            _training_state["progress"] = 100
            _training_state["service_level"] = results.get("service_level", 0)

            # Reload scenario engine params after training
            try:
                import scenario_engine
                scenario_engine.DEFAULT_PARAMS = scenario_engine._load_env_params()
            except Exception:
                pass
        except Exception as e:
            _training_state["status"] = f"error: {str(e)}"

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return {"message": "Training started with real DataCo data", "episodes": episodes}


@router.get("/status")
def training_status():
    """Get current training status."""
    return _training_state


@router.get("/results")
def get_results():
    """Get saved training results."""
    results = get_saved_results()
    if not results:
        raise HTTPException(status_code=404, detail="No training results found. Run training first.")
    return results
