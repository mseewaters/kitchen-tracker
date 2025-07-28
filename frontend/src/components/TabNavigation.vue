<template>
  <div class="tab-nav">
    <button 
      v-for="tab in tabs" 
      :key="tab"
      class="tab-button"
      :class="{ active: activeTab === tab }"
      @click="setActiveTab(tab)"
    >
      {{ tab }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useKitchenStore } from '../stores/kitchen'

const store = useKitchenStore()
const { activeTab } = storeToRefs(store)
const { setActiveTab } = store

const tabs = ['Activities', 'Meals', 'Add tasks']
</script>

<style scoped>
.tab-nav {
  display: flex;
  background: var(--bg-tab-nav);
}

.tab-button {
  flex: 1;
  padding: 16px 24px;
  border: none;
  background: none;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-white-light);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: var(--transition-normal);
}

.tab-button.active {
  color: var(--text-white);
  background: var(--bg-tab-active);
  border-bottom-color: var(--accent-red);
}

.tab-button:hover:not(.active) {
  background: rgba(255,255,255,0.1);
  color: var(--text-white);
}
</style>