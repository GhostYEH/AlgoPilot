<script setup lang="ts">
withDefaults(
  defineProps<{
    iconOnly?: boolean
    size?: 'auth' | 'nav' | 'teacher'
    showSubtitle?: boolean
    title?: string
    subtitle?: string
  }>(),
  {
    iconOnly: false,
    size: 'nav',
    showSubtitle: false,
    title: 'AlgoPilot',
    subtitle: '算法智能学习平台',
  },
)
</script>

<template>
  <div class="brand-logo" :class="`brand-logo--${size}`">
    <img
      class="brand-logo__icon"
      src="/brand/algopilot-icon.png"
      :alt="iconOnly ? 'AlgoPilot' : ''"
      :aria-hidden="iconOnly ? undefined : true"
    />
    <div v-if="!iconOnly" class="brand-logo__text">
      <span class="brand-logo__title">{{ title }}</span>
      <span v-if="showSubtitle" class="brand-logo__subtitle">{{ subtitle }}</span>
    </div>
  </div>
</template>

<style scoped>
.brand-logo {
  --brand-logo-icon-size: 32px;
  --brand-logo-gap: 9px;
  --brand-logo-title-size: 17px;
  --brand-logo-title-weight: 600;
  --brand-logo-title-color: var(--alp-color-text, #334155);
  --brand-logo-subtitle-size: 11px;
  --brand-logo-subtitle-color: var(--alp-color-muted, #64748b);
  display: inline-flex;
  align-items: center;
  gap: var(--brand-logo-gap);
  min-width: 0;
  color: var(--brand-logo-title-color);
}

.brand-logo--auth {
  --brand-logo-icon-size: 38px;
  --brand-logo-gap: 11px;
  --brand-logo-title-size: 14px;
  --brand-logo-title-weight: 650;
  --brand-logo-title-color: var(--auth-ink, #15211e);
  --brand-logo-subtitle-color: var(--auth-muted, #5d6b67);
}

.brand-logo--teacher {
  --brand-logo-icon-size: 30px;
  --brand-logo-gap: 10px;
}

.brand-logo__icon {
  display: block;
  width: var(--brand-logo-icon-size);
  height: var(--brand-logo-icon-size);
  flex: 0 0 auto;
  object-fit: contain;
}

.brand-logo__text {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1px;
  line-height: 1.15;
}

.brand-logo__title {
  overflow: hidden;
  color: var(--brand-logo-title-color);
  font-size: var(--brand-logo-title-size);
  font-weight: var(--brand-logo-title-weight);
  letter-spacing: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-logo__subtitle {
  color: var(--brand-logo-subtitle-color);
  font-size: var(--brand-logo-subtitle-size);
  line-height: 1.35;
  white-space: nowrap;
}
</style>
