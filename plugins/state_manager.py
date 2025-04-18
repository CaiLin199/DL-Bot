class StateManager:
    def __init__(self):
        self.user_states = {}
        self.user_data = {}
    
    def set_state(self, user_id: int, state: str):
        self.user_states[user_id] = state
    
    def get_state(self, user_id: int) -> str:
        return self.user_states.get(user_id)
    
    def clear_state(self, user_id: int):
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.user_data:
            del self.user_data[user_id]
    
    def set_data(self, user_id: int, key: str, value: str):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id][key] = value
    
    def get_data(self, user_id: int, key: str) -> str:
        return self.user_data.get(user_id, {}).get(key)
    
    def get_all_data(self, user_id: int) -> dict:
        return self.user_data.get(user_id, {})

# Create a global instance
state_manager = StateManager()