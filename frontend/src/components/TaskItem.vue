<template>
  <div 
    class="task-item"
    :class="{ 
      completed: task.completed, 
      overdue: task.overdue && !task.completed 
    }"
  >
    <div 
      class="task-checkbox"
      :class="{ checked: task.completed }"
      @click="$emit('toggle', task.id)"
    >
      <span v-if="task.completed" class="checkmark">✓</span>
    </div>
    <div class="task-info">
      <div class="task-name">{{ task.name }}</div>
      <div 
        v-if="task.time"
        class="task-time"
        :class="{ 
          overdue: task.overdue && !task.completed,
          completed: task.completed 
        }"
      >
        {{ task.completed ? 'Just completed' : task.time }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Task {
  id: string
  name: string
  time?: string
  completed: boolean
  overdue: boolean
  personId: string
}

defineProps<{
  task: Task
}>()

defineEmits<{
  toggle: [taskId: string]
}>()
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