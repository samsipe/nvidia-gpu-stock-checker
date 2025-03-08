import json
import os
import logging
from datetime import datetime, timedelta

from config import STATE_FILE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StateManager:
    """Class to manage the shared state between components"""

    # Define default state structure as a class variable for consistency
    DEFAULT_STATE = {
        "available": False,
        "subscribers": [],
        "last_message_date": None
    }

    def __init__(self, state_file=STATE_FILE):
        self.state_file = state_file

    def load_state(self):
        """Load current state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logging.debug(f"Loaded state: {state}")

                    # Ensure state has expected structure
                    for key, default_value in self.DEFAULT_STATE.items():
                        if key not in state:
                            state[key] = default_value

                    return state
            except Exception as e:
                logging.error(f"Error loading state: {e}")
                return self.DEFAULT_STATE.copy()

        logging.debug("No state file found, returning default state.")
        return self.DEFAULT_STATE.copy()

    def save_state(self, state):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
                logging.debug(f"Saved state: {state}")
        except Exception as e:
            logging.error(f"Error saving state: {e}")

    def update_stock_state(self, available):
        """Update only the stock portion of the state"""
        state = self.load_state()

        # Check if state changed
        previous_available = state.get("available", False)
        state_changed = available != previous_available

        # Update stock state
        state["available"] = available

        self.save_state(state)
        return state_changed

    def get_stock_state(self):
        """Get current stock state"""
        state = self.load_state()
        return {
            "available": state["available"]
        }

    def add_subscriber(self, phone_number):
        """Add a subscriber to the state"""
        state = self.load_state()

        if phone_number not in state["subscribers"]:
            state["subscribers"].append(phone_number)
            self.save_state(state)
            logging.info(f"Added new subscriber: {phone_number}")
            return True

        logging.info(f"Subscriber already exists: {phone_number}")
        return False

    def remove_subscriber(self, phone_number):
        """Remove a subscriber from the state"""
        state = self.load_state()

        if phone_number in state["subscribers"]:
            state["subscribers"].remove(phone_number)
            self.save_state(state)
            logging.info(f"Removed subscriber: {phone_number}")
            return True

        logging.info(f"Subscriber not found: {phone_number}")
        return False

    def get_subscribers(self):
        """Get all subscribers"""
        state = self.load_state()
        return state["subscribers"]

    def update_last_message_date(self, date):
        """Update the last message date checked"""
        state = self.load_state()
        state["last_message_date"] = date
        self.save_state(state)

    def get_last_message_date(self):
        """Get the last message date checked, defaulting to one hour ago if not set"""
        state = self.load_state()
        if state["last_message_date"] is None:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            return one_hour_ago.isoformat() + "+00:00"
        return state["last_message_date"]
