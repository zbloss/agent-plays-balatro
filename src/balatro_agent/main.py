#!/usr/bin/env python3
"""
Main entry point for the Balatro agent fleet.

This script provides a command-line interface to run the agents that play Balatro.
"""

import asyncio
import argparse
import sys
import traceback
from pathlib import Path

from balatro_agent.agents import CoordinatorAgent
from balatro_agent.config import Config


async def main():
    """Main function to run the Balatro agent fleet."""
    parser = argparse.ArgumentParser(description="Balatro Agent Fleet")
    parser.add_argument("--calibrate", action="store_true", 
                       help="Run system calibration before starting")
    parser.add_argument("--dry-run", action="store_true",
                       help="Test the system without actually playing")
    parser.add_argument("--risk-tolerance", type=float, default=0.5,
                       help="Risk tolerance for strategy (0.0-1.0)")
    parser.add_argument("--memory-dir", type=str, default="./memory",
                       help="Directory to store game memory")
    
    args = parser.parse_args()
    
    print("🃏 Balatro Agent Fleet Starting...")
    print("=" * 50)
    
    try:
        # Initialize the coordinator
        coordinator = CoordinatorAgent()
        
        # Set risk tolerance
        coordinator.strategy_agent.risk_tolerance = args.risk_tolerance
        
        # Set memory directory
        coordinator.memory_agent.memory_dir = Path(args.memory_dir)
        coordinator.memory_agent.memory_dir.mkdir(exist_ok=True)
        
        print(f"📊 Risk Tolerance: {args.risk_tolerance}")
        print(f"🧠 Memory Directory: {args.memory_dir}")
        print(f"🎮 Configuration: {coordinator.config}")
        
        # Calibration phase
        if args.calibrate:
            print("\n🔧 Running system calibration...")
            calibration_result = await coordinator.calibrate_system()
            
            if "error" in calibration_result:
                print(f"❌ Calibration failed: {calibration_result['error']}")
                return 1
            
            print("✅ Calibration completed successfully!")
            print(f"📸 Screenshot saved: {calibration_result.get('screenshot_path', 'None')}")
            
            if args.dry_run:
                print("🏃 Dry run mode - exiting after calibration")
                return 0
        
        # Start game session
        print("\n🎮 Starting game session...")
        session_started = await coordinator.start_game_session()
        
        if not session_started:
            print("❌ Failed to start game session")
            return 1
        
        # Run the main game loop
        print("\n🚀 Starting main game loop...")
        print("=" * 50)
        
        game_result = await coordinator.run_game_loop()
        
        # Display results
        print("\n🏁 Game Session Results:")
        print("=" * 50)
        print(f"✅ Success: {game_result['success']}")
        print(f"🎯 Final Score: {game_result['final_score']}")
        print(f"📈 Final Ante: {game_result['final_ante']}")
        print(f"🎪 Total Decisions: {game_result['total_decisions']}")
        
        if game_result['errors']:
            print(f"⚠️ Errors: {len(game_result['errors'])}")
            for i, error in enumerate(game_result['errors'][:3]):  # Show first 3 errors
                print(f"   {i+1}. {error}")
        
        # Show memory summary
        memory_summary = coordinator.memory_agent.get_memory_summary()
        print(f"\n🧠 Memory Summary:")
        print(f"   Games Played: {memory_summary['total_games']}")
        print(f"   Win Rate: {memory_summary['win_rate']:.2%}")
        print(f"   Tracked Jokers: {memory_summary['tracked_jokers']}")
        
        return 0 if game_result['success'] else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        return 1


def interactive_mode():
    """Interactive mode for testing and development."""
    print("🎮 Balatro Agent Fleet - Interactive Mode")
    print("=" * 50)
    
    coordinator = CoordinatorAgent()
    
    while True:
        print("\nCommands:")
        print("1. Start game session")
        print("2. Calibrate system") 
        print("3. Show system status")
        print("4. Show memory summary")
        print("5. Take screenshot")
        print("q. Quit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == 'q':
            break
        elif choice == '1':
            print("Starting game session...")
            result = asyncio.run(coordinator.start_game_session())
            if result:
                print("Game session started! Use run_game_loop() to continue.")
            else:
                print("Failed to start game session.")
        elif choice == '2':
            print("Running calibration...")
            result = asyncio.run(coordinator.calibrate_system())
            print(f"Calibration result: {result}")
        elif choice == '3':
            status = coordinator.get_system_status()
            print(f"System status: {status}")
        elif choice == '4':
            summary = coordinator.memory_agent.get_memory_summary()
            print(f"Memory summary: {summary}")
        elif choice == '5':
            screenshot_path = coordinator.action_agent.take_screenshot_for_analysis()
            print(f"Screenshot saved: {screenshot_path}")
        else:
            print("Invalid choice")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - run interactive mode
        interactive_mode()
    else:
        # Run with command line arguments
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
