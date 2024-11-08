from collections import deque
from datetime import timedelta

def extractDate(queue_entry):
    return queue_entry[0]
def extractOccurence(queue_entry):
    return queue_entry[3]

class EventQueue:
    def __init__(self, sim_start_date, reoccurences=("daily", "weekly", "monthly", "yearly", "once", "once-dynamic")):
        self.queue_start_date = sim_start_date
        self.event_queues = {recc:[] for recc in reoccurences}
        self.queue_current_indices = {recc:0 for recc in reoccurences}

        self.date_increments = {"daily":timedelta(days=1), "weekly":timedelta(weeks=1)}
    
    def addInitialEvent(self, start_date, reoccurence, class_name, value):
        initial_queue = reoccurence
        # Start in once queue until reoccuring pattern.
        if start_date != self.queue_start_date:
            initial_queue = "once"
        self.event_queues[initial_queue].append((start_date, class_name, value, reoccurence))
    
    def sortQueues(self):
        for reoccurence, queue in self.event_queues.items():
            if reoccurence != "once-dynamic":
                queue.sort(key=extractDate)
                

    def addDynamicEvent(self, start_date, reoccurence, class_name, value):
        queue_entry = (start_date, class_name, value, reoccurence)
        self.event_queues["once-dynamic"].add(queue_entry)

        if start_date < extractDate(self.min_value):
            self.min_value, self.min_freq = (queue_entry, reoccurence)

    def __len__(self):
        return sum(len(queue) for queue in self.event_queues.values())
    
    def returnMinDate(self):
        return extractDate(self.min_value)
    
    def findMin(self):
        min_value = None
        min_value_date = None
        min_freq = None
        for freq, queue in self.event_queues.items():
            if len(queue)>0:
                queue_min_value = None
                if freq != "once-dynamic":
                    queue_min_value = queue[self.queue_current_indices[freq]]
                else:
                    queue_min_value = min(queue)
                
                if min_value_date is None or min_value_date > extractDate(queue_min_value):
                    min_value = queue_min_value
                    min_value_date = extractDate(min_value)
                    min_freq = freq

        return min_value, min_freq
    
    def increment_date(self, date, reoccurence):
        return self.date_increments[reoccurence] + date
    
    def insertAfterCurrent(self, queue_entry, reoccurence):
        self.event_queues[reoccurence].insert(self.queue_current_indices[reoccurence]+1,queue_entry)
    
    def takeMin(self):
        return_value = self.min_value
        if self.min_freq == "once":
            entry_occurence = extractOccurence(return_value)
            if entry_occurence != "once" and entry_occurence != "once-dynamic": # Last case shouldn't be possible but is a stopgap.

                
        elif self.min_freq == "once-dynamic":

        else:
            self.queue_current_indices[self.min_freq] = (self.queue_current_indices[self.min_freq]+1) % len(self.event_queues[self.min_freq])
        self.min_value, self.min_freq = self.findMin()