<template>
  <div 
    class="task-item"
    :class="{ 
      completed: activity.is_completed, 
      overdue: activity.is_overdue && !activity.is_completed 
    }"
  >
    <div 
      class="task-checkbox"
      :class="{ checked: activity.is_completed }"
      @click="$emit('toggle', activity.activity_id)"
    >
      <span v-if="activity.is_completed" class="checkmark">✓</span>
    </div>
    <div class="task-info">
      <div class="task-name">{{ activity.name }}</div>
      <div 
        class="task-time"
        :class="{ 
          overdue: activity.is_overdue && !activity.is_completed,
          completed: activity.is_completed 
        }"
      >
        {{ getTimeDisplay() }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Activity {
  activity_id: string
  name: string
  status: string
  is_completed: boolean
  is_overdue: boolean
  assigned_to: string
  frequency: string
}

const props = defineProps<{
  activity: Activity
}>()

defineEmits<{
  toggle: [activityId: string]
}>()

function getTimeDisplay() {
  if (props.activity.is_completed) {
    return 'Just completed'
  }
  if (props.activity.is_overdue) {
    return 'Overdue'
  }
  return `Due ${props.activity.frequency}`
}
</script>

<style scoped>
.task-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-light);
  transition: var(--transition-normal);
}

.task-item:hover {
  box-shadow: var(--shadow-md);
}

.task-item.completed {
  background: var(--task-bg-completed);
  border-color: var(--task-border-completed);
}

.task-item.overdue {
  background: var(--task-bg-overdue);
  border-color: var(--task-border-overdue);
}

.task-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 50%;
  margin-right: 12px;
  cursor: pointer;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-normal);
}

.task-checkbox.checked {
  background: var(--accent-success);
  border-color: var(--accent-success);
  color: var(--text-white);
}

.task-checkbox:hover:not(.checked) {
  border-color: var(--accent-success);
}

.task-info {
  flex: 1;
}

.task-name {
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.task-time {
  font-size: 12px;
  color: var(--text-light);
}

.task-time.overdue {
  color: var(--red-alert);
}

.task-time.completed {
  color: var(--accent-success);
}

.checkmark {
  font-size: 12px;
  font-weight: 700;
}
</style>