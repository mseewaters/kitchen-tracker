import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

interface Task {
  id: string
  name: string
  time?: string
  completed: boolean
  overdue: boolean
  personId: string
  dueDate?: string
  category?: string
}

interface Person {
  id: string
  name: string
  avatar: string
  avatarClass: string
  tasks: Task[]
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

  // Family and pets data - will be populated from API
  const people = ref<Person[]>([])
  const pets = ref<Person[]>([])
  const loading = ref(false)
  const error = ref('')

  // Computed values
  const allFamily = computed(() => [...people.value, ...pets.value])

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

  // Fetch family members from API (combines people and pets)
  async function fetchFamilyMembers() {
    try {
      loading.value = true
      const response = await fetch(`${apiBaseUrl}/family-members`)
      if (!response.ok) throw new Error('Failed to fetch family members')
      
      const familyData = await response.json()
      
      // Separate people and pets
      people.value = familyData
        .filter((member: any) => member.member_type === 'person')
        .map((person: any) => ({
          id: person.member_id,
          name: person.name,
          avatar: person.name.charAt(0).toUpperCase(),
          avatarClass: `avatar-${person.name.toLowerCase()}`,
          tasks: []
        }))
      
      pets.value = familyData
        .filter((member: any) => member.member_type === 'pet')
        .map((pet: any) => ({
          id: pet.member_id,
          name: pet.name,
          avatar: pet.name.charAt(0).toUpperCase(),
          avatarClass: `avatar-${pet.name.toLowerCase()}`,
          tasks: []
        }))
        
    } catch (err) {
      console.warn('API not available, using mock data for family members')
      // Mock data for development
      people.value = [
        {
          id: 'marjorie',
          name: 'Marjorie',
          avatar: 'M',
          avatarClass: 'avatar-marjorie',
          tasks: []
        },
        {
          id: 'bob',
          name: 'Bob',
          avatar: 'B',
          avatarClass: 'avatar-bob',
          tasks: []
        }
      ]
      
      pets.value = [
        {
          id: 'layla',
          name: 'Layla',
          avatar: 'L',
          avatarClass: 'avatar-layla',
          tasks: []
        },
        {
          id: 'lucy',
          name: 'Lucy',
          avatar: 'L',
          avatarClass: 'avatar-lucy',
          tasks: []
        },
        {
          id: 'sadie',
          name: 'Sadie',
          avatar: 'S',
          avatarClass: 'avatar-sadie',
          tasks: []
        }
      ]
    } finally {
      loading.value = false
    }
  }

  // Fetch activities from API (replaces fetchTasks)
  async function fetchActivities() {
    try {
      loading.value = true
      const response = await fetch(`${apiBaseUrl}/activities`)
      if (!response.ok) throw new Error('Failed to fetch activities')
      
      const activitiesData = await response.json()
      
      // Associate activities with family members
      const allMembers = [...people.value, ...pets.value]
      
      // Clear existing tasks
      allMembers.forEach(member => member.tasks = [])
      
      for (const activity of activitiesData) {
        const member = allMembers.find(m => m.id === activity.assigned_to)
        
        if (member) {
          const taskObj = {
            id: activity.activity_id,
            name: activity.name,
            time: activity.status === 'completed' ? 'Just completed' : `Due ${activity.frequency}`,
            completed: activity.completed,
            overdue: activity.is_overdue,
            personId: activity.assigned_to,
            category: activity.category || 'general'
          }
          
          member.tasks.push(taskObj)
        }
      }
    } catch (err) {
      console.warn('API not available, using mock data for activities')
      // Add some mock tasks to the family members
      const mockTasks = {
        marjorie: [
          { id: 'm1', name: 'Morning Buprioprion', time: '8:30 AM', completed: true, overdue: false, personId: 'marjorie' },
          { id: 'm2', name: 'Lunch Vitamins', time: 'Due 8:00 PM', completed: false, overdue: false, personId: 'marjorie' },
          { id: 'm3', name: 'Clean fish tank', time: 'Overdue', completed: false, overdue: true, personId: 'marjorie' }
        ],
        bob: [
          { id: 'b1', name: 'Morning Pills', time: '8:30 AM', completed: true, overdue: false, personId: 'bob' },
          { id: 'b2', name: 'Evening Pills', time: 'Due 8:00 PM', completed: false, overdue: false, personId: 'bob' }
        ],
        layla: [
          { id: 'l1', name: 'Ate dinner', completed: true, overdue: false, personId: 'layla' },
          { id: 'l2', name: 'Before bed jerky', completed: false, overdue: false, personId: 'layla' }
        ],
        lucy: [
          { id: 'lu1', name: 'Ate dinner', completed: true, overdue: false, personId: 'lucy' },
          { id: 'lu2', name: 'Before bed jerky', completed: false, overdue: false, personId: 'lucy' }
        ],
        sadie: [
          { id: 's1', name: 'Before bed slurp', completed: false, overdue: false, personId: 'sadie' },
          { id: 's2', name: 'Litter box cleaned', completed: false, overdue: false, personId: 'sadie' }
        ]
      }
      
      // Assign mock tasks
      [...people.value, ...pets.value].forEach(member => {
        member.tasks = mockTasks[member.id as keyof typeof mockTasks] || []
      })
      
    } finally {
      loading.value = false
    }
  }

  // Toggle task completion
  async function toggleTask(taskId: string) {
    try {
      // Find the task locally
      let task: Task | undefined
      for (const person of allFamily.value) {
        task = person.tasks.find(t => t.id === taskId)
        if (task) break
      }
      
      if (!task) return
      
      // Update locally first for immediate UI feedback
      const wasCompleted = task.completed
      task.completed = !task.completed
      if (task.completed) {
        task.overdue = false
      }
      
      // Update on server - use new activity completion endpoint
      const endpoint = task.completed 
        ? `${apiBaseUrl}/activities/${taskId}/complete`
        : `${apiBaseUrl}/activities/${taskId}/undo`
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
      
      if (!response.ok) {
        // Revert local change if server update failed
        task.completed = wasCompleted
        throw new Error('Failed to update task')
      }
      
    } catch (err) {
      console.error('Error toggling task:', err)
      error.value = 'Failed to update task'
    }
  }

  function getCompletionStats(personId: string) {
    const person = allFamily.value.find(p => p.id === personId)
    if (!person) return { completed: 0, total: 0, percentage: 0 }
    
    const completed = person.tasks.filter(t => t.completed).length
    const total = person.tasks.length
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
      weather.value.forecast = data.daily.slice(1, 6).map((day: any, index: number) => ({
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
    people,
    pets,
    loading,
    error,
    
    // Computed
    allFamily,
    
    // Actions
    updateDateTime,
    setActiveTab,
    toggleTask,
    getCompletionStats,
    fetchWeather,
    fetchFamilyMembers,
    fetchActivities,
    initializeData
  }
})