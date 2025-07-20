<template>
  <div class="dashboard">
    <!-- Day Name -->
    <div class="day-name">{{ currentDayName }}</div>
    
    <!-- Time -->
    <div class="time">{{ currentTime }}</div>
    
    <!-- Date -->
    <div class="date-section">
      <span class="day">{{ currentDay }}</span>
      <span class="month">{{ currentMonth }}</span>
      <span class="year">{{ currentYear }}</span>
    </div>
    
    <!-- Weather Title -->
    <div class="weather-title">Weather in Cranbury, NJ</div>
    
    <div class="weather-content">
      <!-- Today's Weather Card -->
      <div class="today-card">
        <div class="today-header">Today</div>
        <div v-if="weather.loading" class="loading">Loading weather...</div>
        <div v-else-if="weather.error" class="error">{{ weather.error }}</div>
        <div v-else class="today-content">
          <div class="today-left">
            <div class="temp-line">
              <span class="label">Low:</span>
              <span class="value">{{ weather.today.tempMin }}°F</span>
            </div>
            <div class="temp-line">
              <span class="label">High:</span>
              <span class="value">{{ weather.today.tempMax }}°F</span>
            </div>
            <div class="detail-line">
              <span class="label">Humidity:</span>
              <span class="value">{{ weather.today.humidity }}%</span>
            </div>
            <div class="detail-line">
              <span class="label">Wind:</span>
              <span class="value">{{ weather.today.windSpeed }} mph</span>
            </div>
          </div>
          <div class="today-right">
            <img 
              :src="getWeatherIcon(weather.today.icon)" 
              :alt="weather.today.description"
              class="today-icon"
            />
            <div class="today-description">{{ weather.today.summary }}</div>
          </div>
        </div>
      </div>
      
      <!-- This Week Forecast -->
      <div class="forecast-card">
        <div class="forecast-header">This Week</div>
        <div v-if="!weather.loading && !weather.error" class="forecast-grid">
          <div 
            v-for="day in weather.forecast" 
            :key="day.date"
            class="forecast-day"
          >
            <div class="forecast-day-name">{{ day.dayName }}</div>
            <div class="forecast-icon-container">
              <div 
                class="forecast-icon-circle" 
                :class="getWeatherIconClass(day.icon)"
              >
                <img 
                  :src="getWeatherIcon(day.icon)" 
                  :alt="day.description"
                  class="forecast-icon"
                />
              </div>
            </div>
            <div class="forecast-temp-high">{{ day.tempMax }}°F</div>
            <div class="forecast-temp-low">{{ day.tempMin }}°F</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// Time/Date reactivity
const currentTime = ref('')
const currentDayName = ref('')
const currentDay = ref('')
const currentMonth = ref('')
const currentYear = ref('')
let timeInterval: number

// Weather data
const weather = ref({
  today: {
    tempMax: '',
    tempMin: '',
    icon: '',
    description: '',
    summary: '',
    humidity: '',
    windSpeed: ''
  },
  forecast: [] as Array<{
    date: string,
    dayName: string,
    tempMax: number,
    tempMin: number,
    icon: string,
    description: string
  }>,
  loading: true,
  error: ''
})

// Update time every minute (no seconds)
const updateDateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit',
    hour12: true
  })
  currentDayName.value = now.toLocaleDateString('en-US', { weekday: 'long' })
  currentDay.value = now.getDate().toString()
  currentMonth.value = now.toLocaleDateString('en-US', { month: 'long' })
  currentYear.value = now.getFullYear().toString()
}

// Get weather icon URL from OpenWeatherMap
const getWeatherIcon = (iconCode: string) => {
  return `https://openweathermap.org/img/wn/${iconCode}@2x.png`
}

// Get weather icon class for circular background
const getWeatherIconClass = (iconCode: string) => {
  if (iconCode.includes('01')) return 'sunny' // clear sky
  if (iconCode.includes('02') || iconCode.includes('03') || iconCode.includes('04')) return 'cloudy'
  if (iconCode.includes('09') || iconCode.includes('10')) return 'rainy'
  if (iconCode.includes('11')) return 'stormy'
  if (iconCode.includes('13')) return 'snowy'
  return 'cloudy'
}

// Get day name from date
const getDayName = (dateStr: string, index: number) => {
  if (index === 0) return 'Today'
  if (index === 1) return 'Tomorrow'
  
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { weekday: 'long' })
}

// Fetch weather for Cranbury, NJ using OneCall 3.0 API with daily data
const fetchWeather = async () => {
  try {
    const API_KEY = '34a2be27e7710dca18f4a25ec81ea423'
    // Coordinates for Cranbury, NJ 08512
    const lat = 40.3157
    const lon = -74.5138
    
    const response = await fetch(`https://api.openweathermap.org/data/3.0/onecall?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=imperial&exclude=minutely,hourly,alerts`)
    
    if (!response.ok) {
      throw new Error(`Weather API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Today's weather (first day in daily array)
    const today = data.daily[0]
    weather.value.today = {
      tempMax: Math.round(today.temp.max),
      tempMin: Math.round(today.temp.min),
      icon: today.weather[0].icon,
      description: today.weather[0].description,
      summary: today.summary || today.weather[0].main,
      humidity: today.humidity,
      windSpeed: Math.round(today.wind_speed)
    }
    
    // Next 5 days forecast (skip today, take next 5)
    weather.value.forecast = data.daily.slice(1, 6).map((day: any, index: number) => ({
      date: new Date(day.dt * 1000).toISOString().split('T')[0],
      dayName: getDayName(new Date(day.dt * 1000).toISOString(), index + 1),
      tempMax: Math.round(day.temp.max),
      tempMin: Math.round(day.temp.min),
      icon: day.weather[0].icon,
      description: day.weather[0].description
    }))
    
    weather.value.loading = false
    weather.value.error = ''
    
  } catch (error) {
    console.error('Weather fetch error:', error)
    weather.value.error = 'Failed to load weather data'
    weather.value.loading = false
  }
}

onMounted(() => {
  updateDateTime()
  // Update time every minute instead of every second
  timeInterval = setInterval(updateDateTime, 60000)
  fetchWeather()
})

onUnmounted(() => {
  clearInterval(timeInterval)
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #1a1a1a;
  color: white;
  display: flex;
  flex-direction: column;
  font-family: var(--font-family-primary);
  padding: 1rem 0;
}

/* Top Section - Day/Time/Date - optimized for Fire 10 tablet */
.day-name {
  text-align: center;
  margin: 0.0rem 0;
}

.time {
  text-align: center;
  margin: 0.0rem 0;
}

.date-section {
  text-align: center;
  margin: 0.0rem 0 1.5rem 0;
}

/* Day Name */
.day-name {
  font-size: 3.5rem;
  font-weight: 800;
  color: white;
}

/* Time */
.time {
  font-size: 7.0rem;
  font-weight: 900;
  color: #4ECDC4;
  font-variant-numeric: tabular-nums;
}

/* Date Section */
.date-section {
  font-size: 3.5rem;
  font-weight: 800;
  color: white;
  display: flex;
  justify-content: center;
  gap: 2rem;
  align-items: baseline;
}

.day {
  font-size: 3.5rem;
}

.month {
  font-size: 3.5rem;
}

.year {
  font-size: 3.5rem;
}

/* Weather Title */
.weather-title {
  font-size: 2rem;
  font-weight: 700;
  color: #4ECDC4;
  margin-bottom: 1rem;
  margin-left: 5rem;
  text-align: left;
  padding: 0 1.5rem;
}

/* Weather Content Container */
.weather-content {
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 2rem;
  margin: 0 5rem;
  padding: 0 1.5rem 2.5rem 1.5rem;
  flex: 1;
  align-items: start;
}

/* Today Card */
.today-card {
  background: #e0e0e0;
  border-radius: 15px;
  padding: 1.0rem;
  color: #333;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.today-header {
  font-size: 2.0rem;
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 1rem;
  text-align: left;
}

.today-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
}

.today-left {
  text-align: left;
  flex: 1;
}

.temp-line {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.4rem;
  font-size: 1.8rem;
}

.detail-line {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.4rem;
  font-size: 1.3rem;
}

.temp-line .label {
  font-weight: 700;
  color: #333;
}

.temp-line .value {
  font-weight: 800;
  color: #333;
}

.detail-line .label {
  font-weight: 600;
  color: #555;
}

.detail-line .value {
  font-weight: 700;
  color: #555;
}

.today-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.today-icon {
  width: 120px;
  height: 120px;
  object-fit: cover;
  object-position: center;
  /* This crops out the whitespace around OpenWeatherMap icons */
  transform: scale(1.5);
  margin-bottom: 0.2rem;
}

.today-description {
  font-size: 0.9rem;
  color: #333;
  text-transform: capitalize;
  font-weight: 500;
  max-width: 150px;
  line-height: 1.3;
}

/* Forecast Card */
.forecast-card {
  background: #e0e0e0;
  border-radius: 15px;
  padding: 1.0rem;
  color: #333;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.forecast-header {
  font-size: 2.0rem;
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 0rem;
  text-align: left;
}

.forecast-grid {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex: 1;
  align-items: center;
}

.forecast-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.forecast-day-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1rem;
}

.forecast-icon-container {
  margin-bottom: 0.5rem;
}

.forecast-icon-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.forecast-icon-circle.sunny {
  background: #d6eb61;
}

.forecast-icon-circle.cloudy {
  background: #95A5A6;
}

.forecast-icon-circle.rainy {
  background: #304c88;
}

.forecast-icon-circle.stormy {
  background: #261442;
}

.forecast-icon-circle.snowy {
  background: #ECF0F1;
}

.forecast-icon {
  width: 32px;
  height: 32px;
  object-fit: cover;
  object-position: center;
  /* This crops out the whitespace around OpenWeatherMap icons */
  transform: scale(1.5);
  filter: brightness(0) invert(1);
}

.forecast-temp-high {
  font-size: 1.3rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 0.25rem;
}

.forecast-temp-low {
  font-size: 1.1rem;
  font-weight: 600;
  color: #666;
}

.loading {
  color: #ccc;
  font-style: italic;
  text-align: center;
  padding: 2rem;
}

.error {
  color: #FF6B6B;
  font-weight: 600;
  text-align: center;
  padding: 2rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .dashboard {
    padding: 2rem 1rem;
  }
  
  .day-name {
    font-size: 2.5rem;
  }
  
  .time {
    font-size: 4rem;
  }
  
  .date-section {
    font-size: 2.5rem;
    gap: 1rem;
    flex-wrap: wrap;
  }
  
  .weather-content {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .forecast-grid {
    flex-wrap: wrap;
  }
  
  .today-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .today-left {
    text-align: center;
  }
}
</style>