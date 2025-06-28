#!/usr/bin/env python3
"""
Test script for VLM vision processing.

This script helps debug and test the Vision Language Model functionality.
"""

import asyncio
import sys
from pathlib import Path

from vlm_vision_processor import VLMVisionProcessor


async def test_vlm_basic():
    """Test basic VLM functionality."""
    print("🔬 Testing VLM Basic Functionality")
    print("=" * 40)
    
    processor = VLMVisionProcessor()
    
    if not processor.vlm_model:
        print("❌ VLM not initialized properly")
        return False
    
    print("✅ VLM initialized successfully")
    return True


async def test_screenshot_analysis():
    """Test screenshot analysis."""
    print("\n📸 Testing Screenshot Analysis")
    print("=" * 40)
    
    processor = VLMVisionProcessor()
    
    # Take a screenshot
    print("Taking screenshot...")
    screenshot = processor.take_screenshot()
    print(f"Screenshot shape: {screenshot.shape}")
    
    # Test game state analysis
    print("Analyzing game state...")
    try:
        game_state = await processor.analyze_full_game_state(screenshot)
        print("✅ Game state analysis successful")
        print(f"Result: {game_state}")
        return True
    except Exception as e:
        print(f"❌ Game state analysis failed: {e}")
        return False


async def test_card_detection():
    """Test card detection specifically."""
    print("\n🃏 Testing Card Detection")
    print("=" * 40)
    
    processor = VLMVisionProcessor()
    
    screenshot = processor.take_screenshot()
    
    try:
        cards = await processor.detect_cards_in_hand(screenshot)
        print(f"✅ Detected {len(cards)} cards")
        
        for i, card in enumerate(cards):
            print(f"  Card {i+1}: {card.rank.value} of {card.suit.value}")
        
        return True
    except Exception as e:
        print(f"❌ Card detection failed: {e}")
        return False


async def test_joker_detection():
    """Test joker detection."""
    print("\n🃏 Testing Joker Detection")
    print("=" * 40)
    
    processor = VLMVisionProcessor()
    
    screenshot = processor.take_screenshot()
    
    try:
        jokers = await processor.detect_jokers(screenshot)
        print(f"✅ Detected {len(jokers)} jokers")
        
        for i, joker in enumerate(jokers):
            print(f"  Joker {i+1}: {joker.name} - {joker.description}")
        
        return True
    except Exception as e:
        print(f"❌ Joker detection failed: {e}")
        return False


async def test_game_phase_detection():
    """Test game phase detection."""
    print("\n🎮 Testing Game Phase Detection")
    print("=" * 40)
    
    processor = VLMVisionProcessor()
    
    screenshot = processor.take_screenshot()
    
    try:
        phase = await processor.identify_game_phase(screenshot)
        print(f"✅ Detected game phase: {phase}")
        return True
    except Exception as e:
        print(f"❌ Game phase detection failed: {e}")
        return False


async def test_stats_extraction():
    """Test stats extraction."""
    print("\n📊 Testing Stats Extraction")
    print("=" * 40)
    
    processor = VLMVisionProcessor()
    
    screenshot = processor.take_screenshot()
    
    try:
        stats = await processor.extract_game_stats(screenshot)
        print("✅ Stats extraction successful")
        print(f"Stats: {stats}")
        return True
    except Exception as e:
        print(f"❌ Stats extraction failed: {e}")
        return False


async def run_all_tests():
    """Run all VLM tests."""
    print("🚀 Starting VLM Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic VLM", test_vlm_basic),
        ("Screenshot Analysis", test_screenshot_analysis),
        ("Card Detection", test_card_detection),
        ("Joker Detection", test_joker_detection),
        ("Game Phase Detection", test_game_phase_detection),
        ("Stats Extraction", test_stats_extraction),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1


async def interactive_test():
    """Interactive testing mode."""
    print("🎮 VLM Interactive Test Mode")
    print("=" * 50)
    
    processor = VLMVisionProcessor()
    
    while True:
        print("\nAvailable tests:")
        print("1. Take screenshot and analyze")
        print("2. Detect cards in hand")
        print("3. Detect jokers")
        print("4. Identify game phase")
        print("5. Extract game stats")
        print("6. Full game state analysis")
        print("q. Quit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == 'q':
            break
        elif choice == '1':
            screenshot = processor.take_screenshot()
            print(f"Screenshot taken: {screenshot.shape}")
        elif choice == '2':
            await test_card_detection()
        elif choice == '3':
            await test_joker_detection()
        elif choice == '4':
            await test_game_phase_detection()
        elif choice == '5':
            await test_stats_extraction()
        elif choice == '6':
            await test_screenshot_analysis()
        else:
            print("Invalid choice")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_test())
    else:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
