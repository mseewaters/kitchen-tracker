import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

interface Activity {
  activity_id: string
  name: string
  assigned_to: string
  frequency: string
  status: string
  is_overdue: boolean
  is_completed: boolean
  category?: string
}

interface FamilyMember {
  member_id: string
  name: string
  member_type: 'person' | 'pet'
  pet_type?: string
  is_active: boolean
  avatar: string
  avatarClass: string
  activities: Activity[]
}

interface WeatherData {
  today: {
    tempMax: number
    tempMin: number
    icon: string
    description: string
    summary: string
    humidity: number
    windSpeed: number
  }
  forecast: Array<{
    date: string
    dayName: string
    tempMax: number
    tempMin: number
    icon: string
    description: string
  }>
  loading: boolean
  error: string
}

export const useKitchenStore = defineStore('kitchen', () => {
  // Current time and date
  const currentTime = ref('')
  const currentDayName = ref('')
  const currentDay = ref('')
  const currentMonth = ref('')
  const currentYear = ref('')

  // Active tab
  const activeTab = ref('Activities')

  // Weather data
  const weather = ref<WeatherData>({
    today: {
      tempMax: 0,
      tempMin: 0,
      icon: '',
      description: '',
      summary: '',
      humidity: 0,
      windSpeed: 0
    },
    forecast: [],
    loading: true,
    error: ''
  })

  // Family members data - will be populated from API
  const familyMembers = ref<FamilyMember[]>([])
  const loading = ref(false)
  const error = ref('')

  // Computed values
  const allFamily = computed(() => familyMembers.value)
  const people = computed(() => familyMembers.value.filter(m => m.member_type === 'person'))
  const pets = computed(() => familyMembers.value.filter(m => m.member_type === 'pet'))

  // Actions
  function updateDateTime() {
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

  function setActiveTab(tab: string) {
    activeTab.value = tab
  }

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

  // Fetch family members from API (unified people and pets)
  async function fetchFamilyMembers() {
    try {
      loading.value = true
      const response = await fetch(`${apiBaseUrl}/family-members`)
      if (!response.ok) throw new Error('Failed to fetch family members')
      
      const familyData = await response.json()
      
      familyMembers.value = familyData.map((member: FamilyMember) => ({
        member_id: member.member_id,
        name: member.name,
        member_type: member.member_type,
        pet_type: member.pet_type,
        is_active: member.is_active,
        avatar: member.name.charAt(0).toUpperCase(),
        avatarClass: `avatar-${member.name.toLowerCase()}`,
        activities: []
      }))
        
    } catch {
      console.warn('API not available - family members will be empty until API is accessible')
      familyMembers.value = []
    } finally {
      loading.value = false
    }
  }

  // Fetch activities from API
  async function fetchActivities() {
    try {
      loading.value = true
      const response = await fetch(`${apiBaseUrl}/activities`)
      if (!response.ok) throw new Error('Failed to fetch activities')
      
      const activitiesData = await response.json()
      
      // Clear existing activities
      familyMembers.value.forEach(member => member.activities = [])
      
      for (const activity of activitiesData) {
        const member = familyMembers.value.find(m => m.member_id === activity.assigned_to)
        
        if (member) {
          const activityObj = {
            activity_id: activity.activity_id,
            name: activity.name,
            assigned_to: activity.assigned_to,
            frequency: activity.frequency,
            status: activity.status,
            is_overdue: activity.is_overdue,
            is_completed: activity.is_completed,
            category: activity.category || 'general'
          }
          
          member.activities.push(activityObj)
        }
      }
    } catch {
      console.warn('API not available - activities will be empty until API is accessible')
      // Clear all activities when API is not available
      familyMembers.value.forEach(member => {
        member.activities = []
      })
      
    } finally {
      loading.value = false
    }
  }

  // Toggle activity completion
  async function toggleActivity(activityId: string) {
    try {
      // Find the activity locally
      let activity: Activity | undefined
      for (const member of familyMembers.value) {
        activity = member.activities.find(a => a.activity_id === activityId)
        if (activity) break
      }
      
      if (!activity) return
      
      // Update locally first for immediate UI feedback
      const wasCompleted = activity.is_completed
      activity.is_completed = !activity.is_completed
      activity.status = activity.is_completed ? 'completed' : 'due'
      if (activity.is_completed) {
        activity.is_overdue = false
      }
      
      // Update on server
      const endpoint = activity.is_completed 
        ? `${apiBaseUrl}/activities/${activityId}/complete`
        : `${apiBaseUrl}/activities/${activityId}/undo`
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
      
      if (!response.ok) {
        // Revert local change if server update failed
        activity.is_completed = wasCompleted
        activity.status = wasCompleted ? 'completed' : 'due'
        throw new Error('Failed to update activity')
      }
      
    } catch (err) {
      console.error('Error toggling activity:', err)
      error.value = 'Failed to update activity'
    }
  }

  function getCompletionStats(memberId: string) {
    const member = familyMembers.value.find(m => m.member_id === memberId)
    if (!member) return { completed: 0, total: 0, percentage: 0 }
    
    const completed = member.activities.filter(a => a.is_completed).length
    const total = member.activities.length
    const percentage = total > 0 ? completed / total : 0
    
    return { completed, total, percentage }
  }

  async function fetchWeather(apiKey: string) {
    try {
      weather.value.loading = true
      weather.value.error = ''
      
      // Coordinates for Cranbury, NJ 08512
      const lat = 40.3157
      const lon = -74.5138
      
      const response = await fetch(`https://api.openweathermap.org/data/3.0/onecall?lat=${lat}&lon=${lon}&appid=${apiKey}&units=imperial&exclude=minutely,hourly,alerts`)
      
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
      weather.value.forecast = data.daily.slice(1, 6).map((day: { dt: number; temp: { max: number; min: number }; weather: Array<{ icon: string; description: string }> }, index: number) => ({
        date: new Date(day.dt * 1000).toISOString().split('T')[0],
        dayName: getDayName(new Date(day.dt * 1000).toISOString(), index + 1),
        tempMax: Math.round(day.temp.max),
        tempMin: Math.round(day.temp.min),
        icon: day.weather[0].icon,
        description: day.weather[0].description
      }))
      
      weather.value.loading = false
      
    } catch (error) {
      console.error('Weather fetch error:', error)
      weather.value.error = 'Failed to load weather data'
      weather.value.loading = false
    }
  }

  function getDayName(dateStr: string, index: number) {
    if (index === 1) return 'Tomorrow'
    
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { weekday: 'long' })
  }

  // Initialize data
  async function initializeData() {
    await fetchFamilyMembers()  // Fetch family members (people and pets combined)
    await fetchActivities()     // Fetch activities after family members are loaded
  }

  return {
    // State
    currentTime,
    currentDayName,
    currentDay,
    currentMonth,
    currentYear,
    activeTab,
    weather,
    familyMembers,
    loading,
    error,
    
    // Computed
    allFamily,
    people,
    pets,
    
    // Actions
    updateDateTime,
    setActiveTab,
    toggleActivity,
    getCompletionStats,
    fetchWeather,
    fetchFamilyMembers,
    fetchActivities,
    initializeData
  }
})