from collections import defaultdict
from datetime import datetime, timedelta

class UserRequests:
    def __init__(self, max_requests: int):
        self.requests = defaultdict(list)
        self.max_requests = max_requests
    
    def add_request(self, user_id: int) -> bool:
        now = datetime.now()
        self.requests[user_id] = [
            timestamp for timestamp in self.requests[user_id]
            if now - timestamp < timedelta(days=1)
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_remaining_requests(self, user_id: int) -> int:
        now = datetime.now()
        self.requests[user_id] = [
            timestamp for timestamp in self.requests[user_id]
            if now - timestamp < timedelta(days=1)
        ]
        return self.max_requests - len(self.requests[user_id])
