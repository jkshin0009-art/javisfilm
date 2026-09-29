"""chatup: upgrade parts for the film_assistant looping multi-party chatbot.

Uses the chatbot's existing LLM server and its dots.tts lane; adds
  decide  - Jev-style typed decisions read from the LLM's next-token probabilities
  judge   - the conversation decisions (who speaks, whether to speak, what to do)
  shaper  - raw stream -> speakable clauses (think/special tokens, tags, Korean splitting)
  policy  - end-on-question, turn caps, repetition guard
  voice   - per-character, per-emotion dots.tts reference voices, barge-in queue
  loop    - a reference loop wiring the above
"""
__version__ = "0.1.0"
