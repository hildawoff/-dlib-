<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="modal-overlay" @click.self="close">
        <div class="modal-content">
          <button class="close-btn" @click="close">&times;</button>

          <form @submit.prevent="handleSubmit">
            <!-- USERNAME / EMAIL -->
            <div class="field-group">
              <label>USERNAME</label>
              <input v-model="form.username" type="text" required />
            </div>

            <!-- PASSWORD -->
            <div class="field-group">
              <label>PASSWORD</label>
              <input v-model="form.password" type="password" required />
            </div>

            <!-- Actions row -->
            <div class="actions-row">
              <button type="submit" class="go-btn">Go</button>
              <a href="#" class="forgot-link" @click.prevent>Forgot Password?</a>
            </div>

            <!-- Toggle / register -->
            <div class="fb-row">
              <button type="button" class="fb-btn" @click.prevent="toggleMode">
                {{ mode === 'login' ? '还没有账号？立即注册' : '已有账号？去登录' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useUserStore } from '../stores/user'
import { useAuthModalStore } from '../stores/authModal'

const props = defineProps({
  visible: Boolean,
  mode: { type: String, default: 'login' }
})
const emit = defineEmits(['update:visible', 'update:mode'])

const userStore = useUserStore()
const authModal = useAuthModalStore()

const form = reactive({ username: '', password: '' })

const close = () => {
  emit('update:visible', false)
}

const toggleMode = () => {
  const newMode = props.mode === 'login' ? 'register' : 'login'
  emit('update:mode', newMode)
}

const handleSubmit = async () => {
  if (props.mode === 'login') {
    userStore.login({ name: form.username })
  } else {
    userStore.login({ name: form.username })
  }
  close()
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@600;700&display=swap');

/* ── Overlay ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

/* ── Panel ── */
.modal-content {
  position: relative;
  width: 420px;
  padding: 40px 36px 32px;
  /* dark steel-blue with diagonal texture — matches the navbar bg */
  background-color: #2e4255;
  background-image:
    repeating-linear-gradient(
      -45deg,
      rgba(255,255,255,0.025) 0px,
      rgba(255,255,255,0.025) 1px,
      transparent 1px,
      transparent 7px
    );
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  /* no border-radius — square corners like the original */
  border-radius: 0;
}

/* ── Close button ── */
.close-btn {
  position: absolute;
  top: 6px;
  right: 10px;
  background: none;
  border: none;
  font-size: 22px;
  line-height: 1;
  color: rgba(255,255,255,0.4);
  cursor: pointer;
  transition: color .15s;
  padding: 0;
}
.close-btn:hover { color: #fff; }

/* ── Field group ── */
.field-group {
  margin-bottom: 14px;
}

.field-group label {
  display: block;
  font-family: 'Oswald', sans-serif;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #c8d8e4;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.field-group input {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  background: #f2f0ec;
  border: none;
  outline: none;
  font-size: 13px;
  color: #333;
  /* inset shadow for depth */
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.25);
  border-radius: 1px;
}
.field-group input:focus {
  background: #fff;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.18), 0 0 0 2px rgba(90,154,184,0.5);
}

/* ── Actions row (Go + Forgot) ── */
.actions-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}

.go-btn {
  width: 52px;
  height: 32px;
  background: #c0392b;
  color: #fff;
  border: none;
  border-radius: 2px;
  font-family: 'Oswald', sans-serif;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.05em;
  cursor: pointer;
  flex-shrink: 0;
  transition: background .15s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}
.go-btn:hover { background: #e74c3c; }

.forgot-link {
  color: #c8d8e4;
  font-size: 12.5px;
  text-decoration: none;
  font-family: 'Oswald', sans-serif;
  letter-spacing: 0.04em;
  transition: color .15s;
}
.forgot-link:hover { color: #fff; text-decoration: underline; }

/* ── Toggle button ── */
.fb-row { margin-top: 4px; }

.fb-btn {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3b5998;
  color: #fff;
  border: none;
  border-radius: 2px;
  font-family: 'Oswald', sans-serif;
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: 0.06em;
  cursor: pointer;
  transition: background .15s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}
.fb-btn:hover { background: #4a6aaa; }

/* ── Transition ── */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from,
.fade-leave-to     { opacity: 0; }
</style>