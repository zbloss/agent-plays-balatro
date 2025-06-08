# Future Considerations for Balatro Agent Fleet

This document outlines key areas for future development to transform the current game state observation framework into a fully functional Balatro-playing agent.

## 1. Decision-Making Logic (Strategy Engine)

*   **Hand Evaluation:** Develop algorithms to evaluate the strength of the current hand based on poker rules and active joker effects.
*   **Play Selection:** Implement logic to decide which cards to play to maximize score or achieve specific objectives (e.g., clearing a blind).
*   **Discard Strategy:** Create rules for when and which cards to discard to improve the hand.
*   **Joker Prioritization:** Logic to evaluate the utility of different jokers, especially in the shop.
*   **Shop Strategy:** Implement logic for buying cards, jokers, tarot cards, spectral cards, and packs. This includes managing money and considering long-term build strategies.
*   **Risk/Reward Analysis:** For certain jokers or game situations, weigh potential risks against rewards.

## 2. Handling Different Game Phases

The current system primarily focuses on observing the 'in-round' state. Full gameplay requires:

*   **Shop Phase Management:**
    *   Identifying items in the shop.
    *   Interacting with shop buttons (buy, sell, reroll).
*   **Blind Selection:** Identifying and selecting the next blind to play.
*   **Pre-round Setup:** Using items like tarot cards outside of a playing hand.
*   **Post-round Rewards:** Handling booster pack opening, voucher selection, etc.
*   **Game Over / New Run:** Detecting game over states and potentially starting new runs.

## 3. Robust Error Handling and Resilience

*   **Screen Capture Failures:** Implement retries or fallback mechanisms if screen capture fails.
*   **OCR Inaccuracies:**
    *   Develop methods to validate OCR output (e.g., expected formats, checksums).
    *   Implement confidence scores for OCR results and potentially use them in decision-making.
    *   Consider image pre-processing techniques to improve OCR accuracy.
*   **Element Not Found:** Handle cases where expected game elements (cards, jokers, UI buttons) are not found or are obscured.
*   **Unexpected Game States:** Design the agent to gracefully handle unexpected pop-ups, events, or game states not initially accounted for.
*   **Logging and Debugging:** Implement comprehensive logging to track agent behavior, decisions, and errors for easier debugging and improvement.

## 4. Advanced `google-adk` Integration (or alternative UI automation)

*   **UI Interaction:** If `google-adk` or another chosen tool supports it, implement reliable methods for:
    *   Clicking buttons (Play Hand, Discard, Buy, Reroll, Select Blind, etc.).
    *   Dragging and dropping cards (if necessary, though Balatro is mostly click-based).
*   **Precise Element Identification:** Move beyond OCR/region-based identification to more robust element detection if the toolkit allows (e.g., via accessibility APIs or UI tree inspection).

## 5. Learning and Adaptation (Advanced)

*   **Data Collection:** Store game state data, decisions made, and outcomes to enable analysis and learning.
*   **Reinforcement Learning:** Potentially explore RL techniques to train the agent's decision-making policies.
*   **Strategy Adaptation:** Allow the agent to adapt its strategy based on the current set of jokers and encountered challenges.

## 6. Configuration and Extensibility

*   **Configurable Parameters:** Allow tuning of agent behavior (e.g., risk-taking level, preferred joker types) through configuration files.
*   **Plugin System:** For new jokers or game mechanics, design a way to extend the agent's capabilities without rewriting core logic.
