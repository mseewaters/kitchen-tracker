from typing import List, Optional, Dict
from datetime import date, datetime
from .base_repository import BaseRepository

class TaskRepository(BaseRepository):
    """Repository for household task operations"""
    
    def create_task(self, task) -> bool:
        """Create a new household task"""
        data = task.to_dict()
        data['record_type'] = 'task'
        data['user_id'] = task.household_id
        data['item_id'] = task.task_id
        return self.put_item(data)
    
    def get_task(self, household_id: str, task_id: str):
        """Get a specific task by ID"""
        from models.task import TaskItem
        
        data = self.get_item(household_id, task_id)
        if data and data.get('record_type') == 'task':
            return TaskItem.from_dict(data)
        return None
    
    def get_household_tasks(self, household_id: str, active_only: bool = True) -> List:
        """Get all tasks for a household"""
        from models.task import TaskItem
        
        items = self.query_by_user(household_id)
        tasks = []
        
        for item_data in items:
            if item_data.get('record_type') == 'task':
                task = TaskItem.from_dict(item_data)
                
                if not active_only or task.is_active:
                    tasks.append(task)
        
        return tasks
    
    def update_task_status(self, household_id: str, task_id: str, is_active: bool) -> bool:
        """Activate/deactivate a task"""
        task = self.get_task(household_id, task_id)
        if task:
            task.is_active = is_active
            return self.create_task(task)  # Update existing
        return False
    
    def create_task_completion(self, completion) -> bool:
        """Record completing a task"""
        from models.task import TaskCompletionRecord
        
        data = completion.to_dict()
        data['record_type'] = 'task_completion'
        data['user_id'] = completion.household_id
        # Use record_id as DynamoDB key, store original task_id for queries
        data['item_id'] = completion.record_id
        data['original_task_id'] = completion.task_id
        return self.put_item(data)
    
    def get_task_completions(self, household_id: str, task_id: str = None, 
                           date_filter: str = None) -> List:
        """Get task completion records, optionally filtered"""
        from models.task import TaskCompletionRecord
        
        items = self.query_by_user(household_id)
        completions = []
        
        for item_data in items:
            if item_data.get('record_type') == 'task_completion':
                # Check task_id filter
                if task_id and item_data.get('original_task_id') != task_id:
                    continue
                
                # Check date filter
                if (date_filter and 
                    item_data.get('completed_date') != date_filter):
                    continue
                
                # Restore original structure
                completion_data = item_data.copy()
                completion_data['task_id'] = completion_data.get('original_task_id', completion_data['task_id'])
                completions.append(TaskCompletionRecord.from_dict(completion_data))
        
        return completions
    
    def get_last_completion_date(self, household_id: str, task_id: str) -> Optional[date]:
        """Get the last completion date for a specific task"""
        completions = self.get_task_completions(household_id, task_id)
        
        if not completions:
            return None
        
        # Find most recent completion
        latest = max(completions, key=lambda c: c.completed_date)
        return datetime.fromisoformat(latest.completed_date).date()
    
    def get_task_statuses(self, household_id: str) -> List:
        """Get all tasks with their completion status"""
        from models.task import TaskStatus
        
        tasks = self.get_household_tasks(household_id)
        statuses = []
        
        for task in tasks:
            # Get last completion info
            completions = self.get_task_completions(household_id, task.task_id)
            
            last_completed_date = None
            last_completed_by = None
            
            if completions:
                # Find most recent completion
                latest = max(completions, key=lambda c: c.completed_date)
                last_completed_date = datetime.fromisoformat(latest.completed_date).date()
                last_completed_by = latest.completed_by
            
            status = TaskStatus(
                task=task,
                last_completed_date=last_completed_date,
                last_completed_by=last_completed_by
            )
            statuses.append(status)
        
        return statuses
    
    def get_due_today_tasks(self, household_id: str) -> List:
        """Get tasks that are due today"""
        statuses = self.get_task_statuses(household_id)
        return [status for status in statuses if status.is_due_today]
    
    def get_overdue_tasks(self, household_id: str) -> List:
        """Get tasks that are overdue"""
        statuses = self.get_task_statuses(household_id)
        return [status for status in statuses if status.is_overdue]
    
    def get_completed_today_tasks(self, household_id: str) -> List:
        """Get tasks completed today"""
        today = date.today().isoformat()
        completions = self.get_task_completions(household_id, date_filter=today)
        
        # Get task details for each completion
        enriched_completions = []
        for completion in completions:
            task = self.get_task(household_id, completion.task_id)
            if task:
                completion_dict = completion.to_dict()
                completion_dict['task_name'] = task.name
                completion_dict['task_frequency'] = task.frequency
                enriched_completions.append(completion_dict)
        
        return enriched_completions