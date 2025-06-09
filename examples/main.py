from agent_plays_balatro.agents.balatro_master_agent import BalatroMasterAgent, Context, AgentOutput

def main():
    print("Initializing BalatroMasterAgent...")
    # Pass any necessary global config to BalatroMasterAgent if needed
    master_agent = BalatroMasterAgent(config={})

    print("\nExecuting BalatroMasterAgent sequence...")
    # Create an initial context if required by the master agent's execute method
    # The placeholder SequentialAgent creates one if None is passed.
    initial_context = Context(initial_data={"run_id": "test_run_001"})
    final_output: AgentOutput = master_agent.execute(context=initial_context)

    print("\nBalatroMasterAgent execution finished.")
    if final_output.error:
        print(f"Master Agent execution failed: {final_output.error}")
    else:
        print("Master Agent final output data:")
        # The final output data depends on what the last agent in the sequence (PlaceholderActionAgent) returns.
        # For Pydantic models, model_dump_json is good. For dicts, just print.
        if hasattr(final_output.data, 'model_dump_json'):
            print(final_output.data.model_dump_json(indent=2))
        else:
            import json # For pretty printing dicts
            print(json.dumps(final_output.data, indent=2))

        if final_output.artifacts:
            print(f"Master Agent final artifacts: {final_output.artifacts}")

if __name__ == "__main__":
    main()
