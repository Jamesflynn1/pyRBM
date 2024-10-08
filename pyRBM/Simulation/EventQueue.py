from collections import deque

class EventQueue:
    def __init__(self, start_date, reoccurences=("daily", "weekly", "monthly", "yearly", "once", "once-dynamic")):
        self.queue_start_date = start_date
        self.reoccurences = reoccurences
        self.event_queues = {recc:[] for recc in reoccurences}
        self.event_indices = {recc:0 for recc in reoccurences}

        self.min_queue = min_recc
        (date, class_t, value, reoccur)
        self.date_increments = {"daily", "weekly","monthly", "yearly"}
    def addInitialEvent(self, start_date, reoccuring):
        if start_date != self.queue_start_date:
    
    
    def addDynamicEvent(self):

    def __len__(self):
        return sum(len(queue) for queue in self.event_queues.values())
    
    def returnMinDate(self):
        return self.min_date
    
    def findMin(self):
        min_freq = None
        min_freq_date = None
        for freqs, queues in self.event_queues.values():

    def __next__(self):
        return_val = None
        if self.min_queue == "once":
            try:
                return_val =  self.event_queues[self.min_queue].popleft()
            except IndexError:
                return_val = (None, None, None, None)
        else:
            try:
                freq_event_queue = self.event_queues[self.min_queue][0]
                return_val =  freq_event_queue
                freq_event_queue[0] += self.date_increments[self.min_queue]
                freq_event_queue.rotate()

            except IndexError:
                return_val = (None, None, None, None)    
            

        return (return_val[1], return_val[2])
