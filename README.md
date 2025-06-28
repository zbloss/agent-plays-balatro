# 🃏 Balatro Agent Fleet

A sophisticated multi-agent system designed to play Balatro autonomously using computer vision, strategic decision-making, and adaptive learning.

## 🎯 Overview

This project implements a fleet of specialized AI agents that work together to:
- 👁️ **Observe** the game state through computer vision
- 🧠 **Strategize** using poker hand evaluation and joker synergy analysis  
- 🎬 **Execute** actions through automated mouse/keyboard control
- 🧩 **Learn** from past games to improve future performance
- 🎪 **Coordinate** all activities through a master orchestrator

## 🏗️ Architecture

The system consists of 5 specialized agents:

### 1. **Game State Agent**
- Takes screenshots and processes visual game state
- Identifies cards, jokers, shop items, and UI elements
- Maintains comprehensive game state model
- Tracks player stats, hands, discards, and scores

### 2. **Strategy Agent** 
- Evaluates poker hands with joker effects
- Makes strategic decisions (play/discard/shop)
- Calculates hand probabilities and expected values
- Adapts strategy based on ante progression

### 3. **Action Agent**
- Executes decisions through mouse/keyboard automation
- Handles card selection, button clicks, and shop purchases
- Waits for game state transitions
- Provides calibration tools for UI positioning

### 4. **Memory Agent**
- Records game sessions and decision outcomes
- Learns joker performance and hand type effectiveness
- Provides recommendations based on historical data
- Persists knowledge between sessions

### 5. **Coordinator Agent**
- Orchestrates the entire agent fleet
- Manages the game loop and phase transitions
- Handles error recovery and rate limiting
- Provides system monitoring and status

## 🚀 Quick Start

### Prerequisites

1. **Python 3.12+** with UV package manager
2. **Ollama** with required models:
   ```bash
   ollama pull qwen3:4b
   ollama pull gemma3:4b-it-qat
   ollama pull minicpm-v:8b
   ```
3. **Vision Language Model** (via Ollama):
   ```bash
   # Pull the vision-capable model
   ollama pull minicpm-v:8b
   ```
4. **Balatro game** running in windowed mode

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agent-plays-balatro

# Install dependencies
uv sync
```

### Basic Usage

```bash
# Interactive mode (recommended for first time)
python src/balatro_agent/main.py

# Calibration + full game session
python src/balatro_agent/main.py --calibrate

# Dry run (calibration only)
python src/balatro_agent/main.py --calibrate --dry-run

# Adjust risk tolerance (0.0 = conservative, 1.0 = aggressive)
python src/balatro_agent/main.py --risk-tolerance 0.7

# Custom memory directory
python src/balatro_agent/main.py --memory-dir ./my_memory
```

## 🎮 Setup Instructions

### 1. Game Setup
- Launch Balatro in **windowed mode** (not fullscreen)
- Position the window so it's fully visible
- Start a new run and pause at the hand selection screen

### 2. System Calibration
- Run with `--calibrate` flag
- Follow prompts to identify UI element positions:
  - Play button
  - Discard button
  - Shop skip button
  - Reroll button
- The system will save these positions for future use

### 3. Running the Agent
- After calibration, the agent will:
  - Take screenshots to analyze game state
  - Make strategic decisions based on current situation
  - Execute actions through mouse/keyboard automation
  - Learn from outcomes to improve future play

## 🛠️ Configuration

### Environment Variables

Create a `.env` file:
```bash
LLM_API_KEY=your_api_key_here  # If using external LLM
LLM_API_BASE=http://localhost:11434/v1  # Ollama default
DEFAULT_MODEL=qwen3:4b
BALATRO_WIKI_URL=https://balatro.fandom.com/wiki/Balatro
```

### Agent Parameters

- **Risk Tolerance** (0.0-1.0): Controls how aggressively the agent plays
- **Memory Directory**: Where game memories and learned strategies are stored
- **Action Delays**: Timing between mouse clicks and keyboard inputs
- **Decision Timeout**: Maximum time to spend on strategy decisions

## 📊 Performance Monitoring

The system tracks:
- **Win Rate**: Overall success across game sessions
- **Joker Performance**: Which jokers lead to better outcomes
- **Hand Type Effectiveness**: Success rates for different poker hands
- **Strategy Patterns**: Common decision sequences in winning games
- **Ante Progression**: How far the agent typically progresses

## 🧩 Extending the System

### Adding New Agents

1. Create agent class inheriting from `BaseModel`
2. Implement required methods for your agent's specialty
3. Register with the coordinator
4. Update imports in `__init__.py`

### Improving Vision Processing

1. Add new template matching for UI elements
2. Enhance OCR preprocessing
3. Implement better card/joker recognition
4. Add support for different screen resolutions

### Strategy Enhancements

1. Implement more sophisticated joker synergy calculation
2. Add deck tracking and probability analysis
3. Enhance shop purchase optimization
4. Add support for vouchers and booster packs

## 🐛 Troubleshooting

### Common Issues

**"Could not find play button"**
- Run calibration again: `--calibrate`
- Ensure game window is fully visible
- Check that Balatro is in windowed mode

**"VLM not detecting game elements"**
- Ensure minicpm-v:8b model is installed via Ollama
- Verify game window is clearly visible and well-lit
- Check that Ollama is running (ollama serve)

**"Agent making poor decisions"**
- Increase risk tolerance for more aggressive play
- Let the agent learn from more games
- Check that joker effects are being calculated correctly

**"Memory not persisting"**
- Verify memory directory permissions
- Check disk space
- Ensure proper JSON serialization

### Debug Mode

```bash
# Enable debug logging
DEBUG=1 python src/balatro_agent/main.py

# Take manual screenshots for analysis
python -c "from balatro_agent.agents import ActionAgent; ActionAgent().take_screenshot_for_analysis()"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📝 License

This project is for educational and research purposes. Please respect Balatro's terms of service.

## 🙏 Acknowledgments

- **LocalThunk** for creating the amazing game Balatro
- **Autogen** team for the multi-agent framework
- **Ollama** for local LLM infrastructure
- The **Balatro community** for game knowledge and strategies
