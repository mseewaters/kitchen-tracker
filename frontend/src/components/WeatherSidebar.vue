<template>
  <div class="sidebar">
    <div class="datetime-section">
      <div class="day-date">{{ currentDayName }}, {{ currentMonth }} {{ currentDay }}</div>
      <div class="time-display">{{ currentTime }}</div>
    </div>
    
    <div class="weather-section">
      <div v-if="weather.loading" class="loading">Loading...</div>
      <div v-else-if="weather.error" class="error">{{ weather.error }}</div>
      <template v-else>
        <div class="weather-icon">{{ getWeatherEmoji(weather.today.icon) }}</div>
        <div class="weather-desc">{{ weather.today.description }}</div>
        
        <div class="temp-section">
          <div class="temp-high">High: {{ weather.today.tempMax }}°F</div>
          <div class="temp-low">Low: {{ weather.today.tempMin }}°F</div>
        </div>
        
        <div class="weather-details">
          <div>Humidity: {{ weather.today.humidity }}%</div>
          <div>Wind: {{ weather.today.windSpeed }} mph</div>
        </div>
        
        <div class="forecast-section">
          <div 
            v-for="day in weather.forecast" 
            :key="day.date"
            class="forecast-day"
          >
            <div class="forecast-icon">{{ getWeatherEmoji(day.icon) }}</div>
            <div class="forecast-name">{{ day.dayName }}</div>
            <div class="forecast-temps">H: {{ day.tempMax }} L: {{ day.tempMin }}</div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useKitchenStore } from '../stores/kitchen'

const store = useKitchenStore()
const { currentTime, currentDayName, currentDay, currentMonth, weather } = storeToRefs(store)

function getWeatherEmoji(iconCode: string) {
  const iconMap: { [key: string]: string } = {
    '01d': '☀️', '01n': '🌙',
    '02d': '🌤️', '02n': '☁️',
    '03d': '☁️', '03n': '☁️',
    '04d': '☁️', '04n': '☁️',
    '09d': '🌧️', '09n': '🌧️',
    '10d': '🌧️', '10n': '🌧️',
    '11d': '⚡', '11n': '⚡',
    '13d': '❄️', '13n': '❄️',
    '50d': '🌫️', '50n': '🌫️'
  }
  return iconMap[iconCode] || '🌤️'
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  color: var(--text-white);
  padding: 15px 15px;
  display: flex;
  flex-direction: column;
}

.datetime-section {
  margin-bottom: 20px;
  text-align: center;
}

.day-date {
  font-size: 18px;
  color: var(--text-white-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

.time-display {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-white);
  text-shadow: 1px 1px 4px var(--accent-red);
  margin-bottom: 4px;
  line-height: 1;
}

.weather-section {
  background: var(--bg-weather-section);
  border-radius: 12px;
  padding: 10px 10px;
  backdrop-filter: blur(10px);
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.weather-icon {
  font-size: 50px;
  margin-bottom: 0px;
  text-align: center;
}

.weather-desc {
  font-size: 20px;
  color: var(--text-white);
  margin-bottom: 10px;
  text-align: center;
  line-height: 1.4;
  text-transform: capitalize;
}

.temp-section {
  margin-bottom: 0px;
}

.temp-high, .temp-low {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 6px;
}

.temp-high {
  color: var(--text-white);
}

.temp-low {
  color: var(--text-white);
}

.weather-details {
  font-size: 16px;
  color: var(--text-white);
  line-height: 1.6;
  margin-bottom: 5px;
}

.forecast-section {
  border-top: 1px solid var(--border-weather);
  padding-top: 10px;
  padding-bottom: 10px;
}

.forecast-day {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 12px;
}

.forecast-name {
  font-weight: 500;
  min-width: 60px;
  color: var(--text-white-muted);
}

.forecast-icon {
  font-size: 18px;
  margin: 0 0px;
}

.forecast-temps {
  color: var(--text-white-muted);
  text-align: right;
}

.loading, .error {
  text-align: center;
  padding: 20px;
  color: var(--text-white-muted);
}

.error {
  color: var(--accent-red);
}
</style>