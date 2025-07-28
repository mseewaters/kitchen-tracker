<template>
  <div class="container">
    <!-- Left Sidebar -->
    <WeatherSidebar />
    
    <!-- Main Content -->
    <div class="main-content">
      <!-- Tab Navigation -->
      <TabNavigation />
      
      <!-- Content Area -->
      <div class="content-area">
        <div v-if="activeTab === 'Activities'" class="family-grid">
          <!-- Top Row: People -->
          <FamilyCard
            v-for="person in people"
            :key="person.member_id"
            :member="person"
            @toggle-activity="handleToggleActivity"
          />
          
          <!-- Bottom Row: Pets in thirds -->
          <div class="pets-container">
            <FamilyCard
              v-for="pet in pets"
              :key="pet.member_id"
              :member="pet"
              :is-pet="true"
              @toggle-activity="handleToggleActivity"
            />
          </div>
        </div>
        
        <div v-else-if="activeTab === 'Meals'" class="tab-content">
          <h2>Meals Coming Soon</h2>
          <p>Meal tracking functionality will be implemented here.</p>
        </div>
        
        <div v-else-if="activeTab === 'Add tasks'" class="tab-content">
          <h2>Add Tasks Coming Soon</h2>
          <p>Task creation functionality will be implemented here.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import WeatherSidebar from './WeatherSidebar.vue'
import TabNavigation from './TabNavigation.vue'
import FamilyCard from './FamilyCard.vue'
import { useKitchenStore } from '../stores/kitchen'

const store = useKitchenStore()
const { activeTab, people, pets } = storeToRefs(store)
const { updateDateTime, initializeData, toggleActivity, fetchWeather } = store

let timeInterval: number

async function handleToggleActivity(activityId: string) {
  await toggleActivity(activityId)
}

onMounted(async () => {
  // Initialize time updates
  updateDateTime()
  timeInterval = setInterval(updateDateTime, 60000)
  
  // Initialize data from API
  await initializeData()
  
  // Get weather API key from environment or config
  const weatherApiKey = import.meta.env.VITE_WEATHER_API_KEY
  if (weatherApiKey) {
    await fetchWeather(weatherApiKey)
  } else {
    console.warn('Weather API key not found. Set VITE_WEATHER_API_KEY environment variable.')
  }
})

onUnmounted(() => {
  clearInterval(timeInterval)
})
</script>

<style scoped>
.container {
  display: flex;
  width: var(--container-width);
  height: var(--container-height);
  margin: 0 auto;
  background: var(--bg-container);
  box-shadow: 0 0 20px rgba(0,0,0,0.1);
  font-family: var(--font-family-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.content-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--bg-content);
}

.family-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 50% 50%;
  gap: 16px;
  height: 100%;
}

.pets-container {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

.tab-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-primary);
}

.tab-content h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.tab-content p {
  font-size: 1.2rem;
  color: var(--text-muted);
}

/* Responsive adjustments for smaller screens */
@media (max-width: 1280px) {
  .container {
    width: 100vw;
    height: 100vh;
  }
  
  .family-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }
  
  .pets-container {
    grid-template-columns: 1fr;
  }
}
</style>