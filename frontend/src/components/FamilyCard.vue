<template>
  <div class="family-card" :class="{ 'pets-row': isPet }">
    <div class="family-header">
      <div class="family-name-section">
        <div class="family-avatar" :class="member.avatarClass">
          {{ member.avatar }}
        </div>
        <div class="family-name">{{ member.name }}</div>
      </div>
      <div class="progress-ring">
        <svg class="progress-circle" viewBox="0 0 42 42">
          <circle class="progress-bg" cx="21" cy="21" r="20"></circle>
          <circle 
            class="progress-fill" 
            cx="21" 
            cy="21" 
            r="20" 
            :style="{ strokeDashoffset: progressOffset }"
          ></circle>
        </svg>
        <div class="progress-text">{{ completionStats.completed }}/{{ completionStats.total }}</div>
      </div>
    </div>
    <div class="task-list">
      <TaskItem
        v-for="activity in member.activities"
        :key="activity.activity_id"
        :activity="activity"
        @toggle="$emit('toggleActivity', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import TaskItem from './TaskItem.vue'
import { useKitchenStore } from '../stores/kitchen'

interface FamilyMember {
  member_id: string
  name: string
  member_type: 'person' | 'pet'
  avatar: string
  avatarClass: string
  activities: Array<{
    activity_id: string
    name: string
    status: string
    is_completed: boolean
    is_overdue: boolean
    assigned_to: string
  }>
}

const props = defineProps<{
  member: FamilyMember
  isPet?: boolean
}>()

defineEmits<{
  toggleActivity: [activityId: string]
}>()

const store = useKitchenStore()

const completionStats = computed(() => {
  return store.getCompletionStats(props.member.member_id)
})

const progressOffset = computed(() => {
  const circumference = 126
  const offset = circumference - (completionStats.value.percentage * circumference)
  return offset
})
</script>

<style scoped>
.family-card {
  background: var(--bg-card);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-light);
  position: relative;
  transition: var(--transition-slow);
  display: flex;
  flex-direction: column;
}

.family-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.family-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: var(--accent-card-top);
}

.family-card.pets-row {
  grid-column: span 1;
}

.family-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--border-divider);
  flex-shrink: 0;
}

.family-name-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.family-avatar {
  width: var(--avatar-size);
  height: var(--avatar-size);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-white);
  font-weight: 700;
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.family-avatar.avatar-m { background: var(--accent-gradient-m); }
.family-avatar.avatar-marjorie { background: var(--accent-gradient-m); }
.family-avatar.avatar-b { background: var(--accent-gradient-b); }
.family-avatar.avatar-bob { background: var(--accent-gradient-b); }
.family-avatar.avatar-l { background: var(--accent-gradient-l); }
.family-avatar.avatar-layla { background: var(--accent-gradient-l); }
.family-avatar.avatar-lucy { background: var(--accent-gradient-l); }
.family-avatar.avatar-s { background: var(--accent-gradient-s); }
.family-avatar.avatar-sadie { background: var(--accent-gradient-s); }

.family-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.progress-ring {
  width: var(--progress-ring-size);
  height: var(--progress-ring-size);
  position: relative;
}

.progress-circle {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.progress-circle circle {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
}

.progress-bg {
  stroke: #e9ecef;
}

.progress-fill {
  stroke: var(--accent-success);
  stroke-dasharray: 126;
  stroke-dashoffset: 63;
  transition: stroke-dashoffset 0.5s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 20px;
  flex: 1;
  overflow-y: auto;
}

.task-list::-webkit-scrollbar {
  width: 6px;
}

.task-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.task-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.task-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>