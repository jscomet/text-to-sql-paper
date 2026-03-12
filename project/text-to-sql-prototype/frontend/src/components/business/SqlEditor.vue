<script setup lang="ts">
import { ref, computed } from "vue"
import { ElMessage } from "element-plus"

interface Props {
  modelValue: string
  height?: string | number
  placeholder?: string
  readonly?: boolean
  disabled?: boolean
  showFormat?: boolean
  showCopy?: boolean
  showClear?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: "200px",
  placeholder: "请输入SQL语句...",
  readonly: false,
  disabled: false,
  showFormat: true,
  showCopy: true,
  showClear: true,
})

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void
  (e: "run"): void
  (e: "format"): void
}>()

const editorRef = ref<HTMLTextAreaElement>()

const editorHeight = computed(() => {
  if (typeof props.height === "number") {
    return `${props.height}px`
  }
  return props.height
})

const handleInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  emit("update:modelValue", target.value)
}

const handleRun = () => {
  emit("run")
}

const handleFormat = () => {
  emit("format")
  let sql = props.modelValue
  if (!sql.trim()) return

  const keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "GROUP", "ORDER", "BY", "HAVING", "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT"]

  keywords.forEach((kw) => {
    const regex = new RegExp(`\b${kw}\b`, "gi")
    sql = sql.replace(regex, kw)
  })

  sql = sql
    .replace(/\s*SELECT\s+/gi, "\nSELECT ")
    .replace(/\s*FROM\s+/gi, "\nFROM ")
    .replace(/\s*WHERE\s+/gi, "\nWHERE ")
    .replace(/\s*JOIN\s+/gi, "\nJOIN ")
    .replace(/\s*LEFT\s+/gi, "\nLEFT ")
    .replace(/\s*RIGHT\s+/gi, "\nRIGHT ")
    .replace(/\s*INNER\s+/gi, "\nINNER ")
    .replace(/\s*OUTER\s+/gi, "\nOUTER ")
    .replace(/\s*ON\s+/gi, "\n  ON ")
    .replace(/\s*GROUP\s+BY\s+/gi, "\nGROUP BY ")
    .replace(/\s*ORDER\s+BY\s+/gi, "\nORDER BY ")
    .replace(/\s*HAVING\s+/gi, "\nHAVING ")
    .replace(/\s*LIMIT\s+/gi, "\nLIMIT ")
    .replace(/\s*OFFSET\s+/gi, "\nOFFSET ")
    .replace(/\s*UNION\s+/gi, "\nUNION ")
    .trim()

  emit("update:modelValue", sql)
}

const handleCopy = async () => {
  if (!props.modelValue) return
  try {
    await navigator.clipboard.writeText(props.modelValue)
    ElMessage.success("已复制到剪贴板")
  } catch {
    ElMessage.error("复制失败")
  }
}

const handleClear = () => {
  emit("update:modelValue", "")
}

const insertText = (text: string) => {
  const textarea = editorRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = props.modelValue

  const newValue = value.substring(0, start) + text + value.substring(end)
  emit("update:modelValue", newValue)

  setTimeout(() => {
    textarea.selectionStart = textarea.selectionEnd = start + text.length
    textarea.focus()
  }, 0)
}

const focus = () => {
  editorRef.value?.focus()
}

defineExpose({
  insertText,
  focus,
})
</script>

<template>
  <div class="sql-editor">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-button v-if="showFormat" link size="small" @click="handleFormat">
          <el-icon><MagicStick /></el-icon>格式化
        </el-button>
        <el-button v-if="showCopy" link size="small" :disabled="!modelValue" @click="handleCopy">
          <el-icon><DocumentCopy /></el-icon>复制
        </el-button>
        <el-button v-if="showClear" link size="small" :disabled="!modelValue" @click="handleClear">
          <el-icon><Delete /></el-icon>清空
        </el-button>
      </div>
      <div class="toolbar-right">
        <slot name="toolbar-extra" />
      </div>
    </div>
    <textarea
      ref="editorRef"
      :value="modelValue"
      :placeholder="placeholder"
      :readonly="readonly"
      :disabled="disabled"
      class="editor-textarea"
      :style="{ height: editorHeight }"
      spellcheck="false"
      @input="handleInput"
      @keydown.ctrl.enter.prevent="handleRun"
      @keydown.meta.enter.prevent="handleRun"
    />
    <div class="editor-footer">
      <span class="char-count">{{ modelValue.length }} 字符</span>
      <span class="shortcut-hint">Ctrl+Enter 执行</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.sql-editor {
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: #fff;
  overflow: hidden;

  .editor-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-light);
    background: var(--bg-color);

    .toolbar-left {
      display: flex;
      gap: 8px;
    }
  }

  .editor-textarea {
    width: 100%;
    padding: 12px;
    border: none;
    outline: none;
    font-family: "Fira Code", "Consolas", "Monaco", "Courier New", monospace;
    font-size: 14px;
    line-height: 1.6;
    resize: vertical;
    min-height: 100px;

    &:focus {
      background: #fafafa;
    }

    &:disabled {
      background: var(--border-extra-light);
      cursor: not-allowed;
    }
  }

  .editor-footer {
    display: flex;
    justify-content: space-between;
    padding: 6px 12px;
    border-top: 1px solid var(--border-light);
    background: var(--bg-color);
    font-size: 12px;
    color: var(--text-secondary);

    .shortcut-hint {
      font-family: monospace;
    }
  }
}
</style>
