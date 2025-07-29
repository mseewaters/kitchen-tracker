<template>
  <div class="admin-tab">
    <div class="admin-header">
      <h2>Manage Family & Tasks</h2>
      <div class="section-tabs">
        <button 
          class="section-tab"
          :class="{ active: activeSection === 'family' }"
          @click="activeSection = 'family'"
        >
          Family Members
        </button>
        <button 
          class="section-tab"
          :class="{ active: activeSection === 'activities' }"
          @click="activeSection = 'activities'"
        >
          Recurring Tasks
        </button>
      </div>
    </div>

    <!-- Family Members Section -->
    <div v-if="activeSection === 'family'" class="section-content">
      <div class="section-actions">
        <button class="btn-primary" @click="openFamilyMemberForm()">
          Add Family Member
        </button>
      </div>

      <div class="data-table">
        <div class="table-header">
          <div class="col-name">Name</div>
          <div class="col-type">Type</div>
          <div class="col-pet-type">Pet Type</div>
          <div class="col-status">Status</div>
          <div class="col-actions">Actions</div>
        </div>
        
        <div 
          v-for="member in familyMembers" 
          :key="member.member_id"
          class="table-row"
        >
          <div class="col-name">{{ member.name }}</div>
          <div class="col-type">{{ member.member_type }}</div>
          <div class="col-pet-type">{{ member.pet_type || '-' }}</div>
          <div class="col-status">
            <span :class="member.is_active ? 'status-active' : 'status-inactive'">
              {{ member.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="col-actions">
            <button class="btn-edit" @click="openFamilyMemberForm(member)">Edit</button>
            <button class="btn-delete" @click="deleteFamilyMember(member.member_id)">Delete</button>
          </div>
        </div>

        <div v-if="familyMembers.length === 0" class="empty-state">
          No family members found. Add your first family member above.
        </div>
      </div>
    </div>

    <!-- Recurring Activities Section -->
    <div v-if="activeSection === 'activities'" class="section-content">
      <div class="section-actions">
        <button class="btn-primary" @click="openActivityForm()">
          Add Recurring Task
        </button>
      </div>

      <div class="data-table">
        <div class="table-header">
          <div class="col-name">Task Name</div>
          <div class="col-assigned">Assigned To</div>
          <div class="col-frequency">Frequency</div>
          <div class="col-category">Category</div>
          <div class="col-status">Status</div>
          <div class="col-actions">Actions</div>
        </div>
        
        <div 
          v-for="activity in activities" 
          :key="activity.activity_id"
          class="table-row"
        >
          <div class="col-name">{{ activity.name }}</div>
          <div class="col-assigned">{{ getAssignedMemberName(activity.assigned_to) }}</div>
          <div class="col-frequency">{{ activity.frequency }}</div>
          <div class="col-category">{{ activity.category || 'General' }}</div>
          <div class="col-status">
            <span :class="activity.is_active ? 'status-active' : 'status-inactive'">
              {{ activity.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="col-actions">
            <button class="btn-edit" @click="openActivityForm(activity)">Edit</button>
            <button class="btn-delete" @click="deleteActivity(activity.activity_id)">Delete</button>
          </div>
        </div>

        <div v-if="activities.length === 0" class="empty-state">
          No recurring tasks found. Add your first task above.
        </div>
      </div>
    </div>

    <!-- Family Member Form Modal -->
    <div v-if="showFamilyMemberForm" class="modal-overlay" @click="closeFamilyMemberForm">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingFamilyMember ? 'Edit' : 'Add' }} Family Member</h3>
          <button class="modal-close" @click="closeFamilyMemberForm">&times;</button>
        </div>
        
        <form @submit.prevent="saveFamilyMember" class="form">
          <div class="form-group">
            <label for="member-name">Name *</label>
            <input 
              id="member-name"
              v-model="familyMemberForm.name"
              type="text"
              required
              placeholder="Enter name"
            />
          </div>

          <div class="form-group">
            <label for="member-type">Type *</label>
            <select 
              id="member-type"
              v-model="familyMemberForm.member_type"
              required
              @change="onMemberTypeChange"
            >
              <option value="">Select type</option>
              <option value="person">Person</option>
              <option value="pet">Pet</option>
            </select>
          </div>

          <div v-if="familyMemberForm.member_type === 'pet'" class="form-group">
            <label for="pet-type">Pet Type *</label>
            <select 
              id="pet-type"
              v-model="familyMemberForm.pet_type"
              required
            >
              <option value="">Select pet type</option>
              <option value="dog">Dog</option>
              <option value="cat">Cat</option>
              <option value="bird">Bird</option>
              <option value="fish">Fish</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox"
                v-model="familyMemberForm.is_active"
              />
              Active
            </label>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="closeFamilyMemberForm">
              Cancel
            </button>
            <button type="submit" class="btn-primary" :disabled="!familyMemberForm.name || !familyMemberForm.member_type">
              {{ editingFamilyMember ? 'Update' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Activity Form Modal -->
    <div v-if="showActivityForm" class="modal-overlay" @click="closeActivityForm">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingActivity ? 'Edit' : 'Add' }} Recurring Task</h3>
          <button class="modal-close" @click="closeActivityForm">&times;</button>
        </div>
        
        <form @submit.prevent="saveActivity" class="form">
          <div class="form-group">
            <label for="activity-name">Task Name *</label>
            <input 
              id="activity-name"
              v-model="activityForm.name"
              type="text"
              required
              placeholder="Enter task name"
            />
          </div>

          <div class="form-group">
            <label for="assigned-to">Assigned To *</label>
            <select 
              id="assigned-to"
              v-model="activityForm.assigned_to"
              required
            >
              <option value="">Select family member</option>
              <option 
                v-for="member in activeFamilyMembers" 
                :key="member.member_id"
                :value="member.member_id"
              >
                {{ member.name }} ({{ member.member_type }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="frequency">Frequency *</label>
            <select 
              id="frequency"
              v-model="activityForm.frequency"
              required
            >
              <option value="">Select frequency</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div class="form-group">
            <label for="category">Category</label>
            <select 
              id="category"
              v-model="activityForm.category"
            >
              <option value="">Select category</option>
              <option value="medication">Medication</option>
              <option value="feeding">Feeding</option>
              <option value="exercise">Exercise</option>
              <option value="hygiene">Hygiene</option>
              <option value="chores">Chores</option>
              <option value="general">General</option>
            </select>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox"
                v-model="activityForm.is_active"
              />
              Active
            </label>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="closeActivityForm">
              Cancel
            </button>
            <button type="submit" class="btn-primary" :disabled="!isActivityFormValid">
              {{ editingActivity ? 'Update' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useKitchenStore } from '../stores/kitchen'
import api from '../services/api'

interface FamilyMember {
  member_id: string
  name: string
  member_type: 'person' | 'pet'
  pet_type?: string
  is_active: boolean
}

interface RecurringActivity {
  activity_id: string
  name: string
  assigned_to: string
  frequency: string
  category?: string
  is_active: boolean
}

interface FamilyMemberFormData {
  name: string
  member_type: string
  pet_type: string
  is_active: boolean
}

interface ActivityFormData {
  name: string
  assigned_to: string
  frequency: string
  category: string
  is_active: boolean
}

const store = useKitchenStore()
const { familyMembers } = storeToRefs(store)

// Active section
const activeSection = ref<'family' | 'activities'>('family')

// Activities data
const activities = ref<RecurringActivity[]>([])

// Family Member Form
const showFamilyMemberForm = ref(false)
const editingFamilyMember = ref<FamilyMember | null>(null)
const familyMemberForm = ref<FamilyMemberFormData>({
  name: '',
  member_type: '',
  pet_type: '',
  is_active: true
})

// Activity Form
const showActivityForm = ref(false)
const editingActivity = ref<RecurringActivity | null>(null)
const activityForm = ref<ActivityFormData>({
  name: '',
  assigned_to: '',
  frequency: '',
  category: '',
  is_active: true
})

// Computed
const activeFamilyMembers = computed(() => 
  familyMembers.value.filter(m => m.is_active)
)

const isActivityFormValid = computed(() =>
  activityForm.value.name && 
  activityForm.value.assigned_to && 
  activityForm.value.frequency
)

// Methods
function getAssignedMemberName(memberId: string): string {
  const member = familyMembers.value.find(m => m.member_id === memberId)
  return member ? member.name : 'Unknown'
}

function openFamilyMemberForm(member?: FamilyMember) {
  if (member) {
    editingFamilyMember.value = member
    familyMemberForm.value = {
      name: member.name,
      member_type: member.member_type,
      pet_type: member.pet_type || '',
      is_active: member.is_active
    }
  } else {
    editingFamilyMember.value = null
    familyMemberForm.value = {
      name: '',
      member_type: '',
      pet_type: '',
      is_active: true
    }
  }
  showFamilyMemberForm.value = true
}

function closeFamilyMemberForm() {
  showFamilyMemberForm.value = false
  editingFamilyMember.value = null
}

function onMemberTypeChange() {
  if (familyMemberForm.value.member_type === 'person') {
    familyMemberForm.value.pet_type = ''
  }
}

async function saveFamilyMember() {
  try {
    const memberData = {
      name: familyMemberForm.value.name,
      member_type: familyMemberForm.value.member_type,
      pet_type: familyMemberForm.value.member_type === 'pet' ? familyMemberForm.value.pet_type : undefined,
      is_active: familyMemberForm.value.is_active
    }

    if (editingFamilyMember.value) {
      await api.put(`/family-members/${editingFamilyMember.value.member_id}`, memberData)
    } else {
      await api.post('/family-members', memberData)
    }

    closeFamilyMemberForm()
    await store.fetchFamilyMembers()
  } catch (error) {
    console.error('Error saving family member:', error)
    alert('Failed to save family member')
  }
}

async function deleteFamilyMember(memberId: string) {
  if (!confirm('Are you sure you want to delete this family member?')) {
    return
  }

  try {
    await api.delete(`/family-members/${memberId}`)
    await store.fetchFamilyMembers()
  } catch (error) {
    console.error('Error deleting family member:', error)
    alert('Failed to delete family member')
  }
}

function openActivityForm(activity?: RecurringActivity) {
  if (activity) {
    editingActivity.value = activity
    activityForm.value = {
      name: activity.name,
      assigned_to: activity.assigned_to,
      frequency: activity.frequency,
      category: activity.category || '',
      is_active: activity.is_active
    }
  } else {
    editingActivity.value = null
    activityForm.value = {
      name: '',
      assigned_to: '',
      frequency: '',
      category: '',
      is_active: true
    }
  }
  showActivityForm.value = true
}

function closeActivityForm() {
  showActivityForm.value = false
  editingActivity.value = null
}

async function saveActivity() {
  try {
    const activityData = {
      name: activityForm.value.name,
      assigned_to: activityForm.value.assigned_to,
      frequency: activityForm.value.frequency,
      category: activityForm.value.category || undefined,
      is_active: activityForm.value.is_active
    }

    if (editingActivity.value) {
      await api.put(`/activities/${editingActivity.value.activity_id}`, activityData)
    } else {
      await api.post('/activities', activityData)
    }

    closeActivityForm()
    await fetchActivities()
  } catch (error) {
    console.error('Error saving activity:', error)
    alert('Failed to save activity')
  }
}

async function deleteActivity(activityId: string) {
  if (!confirm('Are you sure you want to delete this recurring task?')) {
    return
  }

  try {
    await api.delete(`/activities/${activityId}`)
    await fetchActivities()
  } catch (error) {
    console.error('Error deleting activity:', error)
    alert('Failed to delete activity')
  }
}

async function fetchActivities() {
  try {
    const response = await api.get('/activities')
    activities.value = response.data
  } catch (error) {
    console.error('Error fetching activities:', error)
    activities.value = []
  }
}

onMounted(() => {
  fetchActivities()
})
</script>

<style scoped>
.admin-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  background: var(--bg-content);
  overflow: hidden;
}

.admin-header {
  margin-bottom: 24px;
}

.admin-header h2 {
  color: var(--text-primary);
  margin: 0 0 16px 0;
  font-size: 1.8rem;
}

.section-tabs {
  display: flex;
  gap: 8px;
}

.section-tab {
  padding: 8px 16px;
  border: 2px solid var(--border-light);
  background: var(--bg-card);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.section-tab:hover {
  background: var(--bg-hover);
}

.section-tab.active {
  background: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.section-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-actions {
  margin-bottom: 16px;
}

.data-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-card);
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tab-nav);
  color: var(--text-white);
  font-weight: 600;
  border-bottom: 1px solid var(--border-light);
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
  align-items: center;
}

.table-row:hover {
  background: var(--bg-hover);
}

.table-row:last-child {
  border-bottom: none;
}

.status-active {
  color: var(--status-completed);
  font-weight: 500;
}

.status-inactive {
  color: var(--text-muted);
  font-weight: 500;
}

.col-actions {
  display: flex;
  gap: 8px;
}

.btn-edit, .btn-delete {
  padding: 4px 8px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-edit {
  background: var(--bg-card);
  color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.btn-edit:hover {
  background: var(--accent-blue);
  color: white;
}

.btn-delete {
  background: var(--bg-card);
  color: var(--accent-red);
  border-color: var(--accent-red);
}

.btn-delete:hover {
  background: var(--accent-red);
  color: white;
}

.btn-primary {
  background: var(--accent-blue);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-blue-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: var(--bg-hover);
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
  font-style: italic;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 {
  margin: 0;
  color: var(--text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: var(--text-primary);
}

.form {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-primary);
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  background: var(--bg-content);
  color: var(--text-primary);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto !important;
  margin: 0;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

/* Responsive for activities table */
@media (max-width: 1280px) {
  .table-header,
  .table-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .table-header > div,
  .table-row > div {
    padding: 4px 0;
  }
  
  .col-actions {
    justify-content: flex-start;
  }
}
</style>