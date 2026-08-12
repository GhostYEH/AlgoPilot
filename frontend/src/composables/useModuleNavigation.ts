import { useRouter } from 'vue-router'
import { ALGORITHM_MODULES, MODULE_ROUTE_NAMES } from '@/constants/modules'
import { recordModuleVisit } from '@/utils/learningBookmarks'

export function useModuleNavigation() {
  const router = useRouter()

  function goModule(key: string) {
    const mod = ALGORITHM_MODULES.find((m) => m.key === key)
    if (mod) recordModuleVisit(key, mod.label)
    const routeName = MODULE_ROUTE_NAMES[key]
    if (routeName) {
      router.push({ name: routeName })
      return
    }
    router.push({ name: 'learning-path', query: { module: key } })
  }

  return { goModule }
}
