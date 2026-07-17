<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'
import landTopology from 'world-atlas/land-110m.json'

import {
  createLandPointPositions,
  createLatitudeLine,
  createLongitudeLine,
  latLngToVector3,
} from './login-globe'

const mountRef = ref<HTMLDivElement>()
const isHovered = ref(false)

let animationFrame = 0
let resizeObserver: ResizeObserver | undefined
let renderer: THREE.WebGLRenderer | undefined
let scene: THREE.Scene | undefined
let camera: THREE.OrthographicCamera | undefined
let globeGroup: THREE.Group | undefined
let tiltGroup: THREE.Group | undefined
let reducedMotionQuery: MediaQueryList | undefined
let lastFrameTime = 0
let isPageVisible = !document.hidden
let rotationSpeed = 0.105
let targetRotationSpeed = 0.105
let targetTiltX = 0
let targetTiltY = 0

const lineMaterial = (color: number, opacity: number) =>
  new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity,
    depthTest: true,
    depthWrite: false,
  })

function lineFromPoints(points: THREE.Vector3[], material: THREE.LineBasicMaterial) {
  return new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), material)
}

function createOutline() {
  const points: THREE.Vector3[] = []
  for (let index = 0; index < 192; index += 1) {
    const angle = (index / 192) * Math.PI * 2
    points.push(new THREE.Vector3(Math.cos(angle) * 1.012, Math.sin(angle) * 1.012, 0.012))
  }
  return new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(points),
    lineMaterial(0x405852, 0.43),
  )
}

function createOrbit() {
  const orbitGroup = new THREE.Group()
  const orbitPoints: THREE.Vector3[] = []

  for (let index = 0; index <= 220; index += 1) {
    const angle = (index / 220) * Math.PI * 2
    orbitPoints.push(new THREE.Vector3(Math.cos(angle) * 1.52, 0, Math.sin(angle) * 1.52))
  }

  const orbit = lineFromPoints(orbitPoints, lineMaterial(0x4e6962, 0.26))
  orbitGroup.add(orbit)
  orbitGroup.rotation.x = THREE.MathUtils.degToRad(16)
  orbitGroup.rotation.z = THREE.MathUtils.degToRad(-8)

  const markerAngle = THREE.MathUtils.degToRad(318)
  const markerPosition = new THREE.Vector3(
    Math.cos(markerAngle) * 1.52,
    0,
    Math.sin(markerAngle) * 1.52,
  )
  const markerOuter = new THREE.Mesh(
    new THREE.SphereGeometry(0.042, 16, 12),
    new THREE.MeshBasicMaterial({ color: 0x7f8d89 }),
  )
  const markerInner = new THREE.Mesh(
    new THREE.SphereGeometry(0.031, 16, 12),
    new THREE.MeshBasicMaterial({ color: 0xe9eeeb }),
  )
  markerOuter.position.copy(markerPosition)
  markerInner.position.copy(markerPosition).multiplyScalar(1.014)
  markerInner.scale.setScalar(0.92)
  orbitGroup.add(markerOuter, markerInner)

  return orbitGroup
}

function createNetwork(group: THREE.Group) {
  const nodeDefinitions = [
    { latitude: 16, longitude: -102, color: 0x64a8c1, size: 0.052 },
    { latitude: -4, longitude: -54, color: 0x75b47c, size: 0.052 },
    { latitude: 34, longitude: 24, color: 0xd5a06c, size: 0.054 },
    { latitude: -18, longitude: 52, color: 0xa5aaa8, size: 0.035 },
    { latitude: 18, longitude: 72, color: 0xa5aaa8, size: 0.032 },
  ]
  const nodePositions = nodeDefinitions.map(({ latitude, longitude }) =>
    latLngToVector3(latitude, longitude, 1.035),
  )
  const connections = [
    [0, 1],
    [0, 2],
    [1, 2],
    [1, 3],
    [2, 4],
  ]

  connections.forEach(([startIndex, endIndex]) => {
    const start = nodePositions[startIndex]!
    const end = nodePositions[endIndex]!
    const middle = start.clone().add(end).normalize().multiplyScalar(1.12)
    const curve = new THREE.QuadraticBezierCurve3(start, middle, end)
    group.add(lineFromPoints(curve.getPoints(32), lineMaterial(0x405852, 0.48)))
  })

  nodeDefinitions.forEach(({ color, size }, index) => {
    const position = nodePositions[index]!
    const outer = new THREE.Mesh(
      new THREE.SphereGeometry(size, 18, 14),
      new THREE.MeshBasicMaterial({ color: 0x536760 }),
    )
    const inner = new THREE.Mesh(
      new THREE.SphereGeometry(size * 0.78, 18, 14),
      new THREE.MeshBasicMaterial({ color }),
    )
    outer.position.copy(position)
    inner.position.copy(position).normalize().multiplyScalar(1.035 + size * 0.28)
    group.add(outer, inner)
  })
}

function createScene() {
  const mount = mountRef.value
  if (!mount) return

  scene = new THREE.Scene()
  camera = new THREE.OrthographicCamera(-2.05, 2.05, 2.05, -2.05, 0.1, 20)
  camera.position.set(0, 0, 5)

  renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance',
  })
  renderer.setClearColor(0x000000, 0)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.domElement.className = 'login-globe-canvas'
  renderer.domElement.setAttribute('aria-hidden', 'true')
  mount.appendChild(renderer.domElement)

  tiltGroup = new THREE.Group()
  globeGroup = new THREE.Group()
  globeGroup.rotation.x = THREE.MathUtils.degToRad(-7)
  globeGroup.rotation.y = THREE.MathUtils.degToRad(-28)

  const depthMask = new THREE.Mesh(
    new THREE.SphereGeometry(1, 56, 40),
    new THREE.MeshBasicMaterial({
      colorWrite: false,
      depthWrite: true,
      depthTest: true,
    }),
  )
  depthMask.renderOrder = -2
  globeGroup.add(depthMask)

  const graticuleMaterial = lineMaterial(0x4e6962, 0.2)
  ;[-28, 0, 28].forEach((latitude) => {
    globeGroup?.add(lineFromPoints(createLatitudeLine(latitude), graticuleMaterial))
  })
  ;[-70, 10, 90].forEach((longitude) => {
    globeGroup?.add(lineFromPoints(createLongitudeLine(longitude), graticuleMaterial))
  })

  const landGeometry = new THREE.BufferGeometry()
  landGeometry.setAttribute(
    'position',
    new THREE.BufferAttribute(createLandPointPositions(landTopology), 3),
  )
  const landPoints = new THREE.Points(
    landGeometry,
    new THREE.PointsMaterial({
      color: 0x273b37,
      size: 0.014,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.66,
      depthTest: true,
      depthWrite: false,
    }),
  )
  globeGroup.add(landPoints)
  createNetwork(globeGroup)

  tiltGroup.add(globeGroup)
  scene.add(tiltGroup, createOutline(), createOrbit())

  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(mount)
  resize()
  lastFrameTime = performance.now()
  animationFrame = requestAnimationFrame(renderFrame)
}

function resize() {
  const mount = mountRef.value
  if (!mount || !renderer || !camera) return
  const width = Math.max(1, mount.clientWidth)
  const height = Math.max(1, mount.clientHeight)
  const aspect = width / height
  const verticalSize = 1.6

  camera.left = -verticalSize * aspect
  camera.right = verticalSize * aspect
  camera.top = verticalSize
  camera.bottom = -verticalSize
  camera.updateProjectionMatrix()
  renderer.setSize(width, height, false)
}

function renderFrame(time: number) {
  if (!renderer || !scene || !camera || !globeGroup || !tiltGroup || !isPageVisible) return

  const delta = Math.min((time - lastFrameTime) / 1000, 0.05)
  lastFrameTime = time
  rotationSpeed += (targetRotationSpeed - rotationSpeed) * Math.min(1, delta * 3.2)

  if (!reducedMotionQuery?.matches) {
    globeGroup.rotation.y += rotationSpeed * delta
    tiltGroup.rotation.x += (targetTiltX - tiltGroup.rotation.x) * Math.min(1, delta * 4.6)
    tiltGroup.rotation.y += (targetTiltY - tiltGroup.rotation.y) * Math.min(1, delta * 4.6)
  }

  renderer.render(scene, camera)
  animationFrame = requestAnimationFrame(renderFrame)
}

function handlePointerMove(event: PointerEvent) {
  if (reducedMotionQuery?.matches) return
  const mount = mountRef.value
  if (!mount) return
  const bounds = mount.getBoundingClientRect()
  const normalizedX = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2
  const normalizedY = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2
  targetTiltX = THREE.MathUtils.degToRad(-normalizedY * 2.2)
  targetTiltY = THREE.MathUtils.degToRad(normalizedX * 2.6)
}

function handlePointerEnter() {
  isHovered.value = true
  targetRotationSpeed = reducedMotionQuery?.matches ? 0 : 0.121
}

function handlePointerLeave() {
  isHovered.value = false
  targetRotationSpeed = reducedMotionQuery?.matches ? 0 : 0.105
  targetTiltX = 0
  targetTiltY = 0
}

function handleVisibilityChange() {
  isPageVisible = !document.hidden
  if (!isPageVisible) {
    cancelAnimationFrame(animationFrame)
    return
  }

  lastFrameTime = performance.now()
  animationFrame = requestAnimationFrame(renderFrame)
}

function handleReducedMotionChange() {
  targetRotationSpeed = reducedMotionQuery?.matches ? 0 : isHovered.value ? 0.121 : 0.105
  if (reducedMotionQuery?.matches) {
    targetTiltX = 0
    targetTiltY = 0
  }
}

function renderFallback() {
  const mount = mountRef.value
  if (!mount) return
  const canvas = document.createElement('canvas')
  canvas.className = 'login-globe-canvas login-globe-fallback'
  canvas.width = 720
  canvas.height = 720
  const context = canvas.getContext('2d')
  if (!context) return

  context.scale(2, 2)
  context.translate(180, 180)
  context.strokeStyle = 'rgba(64, 88, 82, 0.42)'
  context.lineWidth = 0.75
  context.beginPath()
  context.arc(0, 0, 104, 0, Math.PI * 2)
  context.stroke()
  context.strokeStyle = 'rgba(78, 105, 98, 0.22)'
  context.beginPath()
  context.ellipse(0, 20, 154, 38, 0.12, 0, Math.PI * 2)
  context.stroke()
  mount.appendChild(canvas)
}

onMounted(() => {
  reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotionQuery.addEventListener('change', handleReducedMotionChange)
  document.addEventListener('visibilitychange', handleVisibilityChange)

  try {
    createScene()
    handleReducedMotionChange()
  } catch {
    renderer?.dispose()
    renderer?.domElement.remove()
    renderer = undefined
    renderFallback()
  }
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  reducedMotionQuery?.removeEventListener('change', handleReducedMotionChange)

  scene?.traverse((object) => {
    if (object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points) {
      object.geometry.dispose()
      const materials = Array.isArray(object.material) ? object.material : [object.material]
      materials.forEach((material) => material.dispose())
    }
  })

  renderer?.dispose()
  renderer?.forceContextLoss()
  renderer?.domElement.remove()
  mountRef.value?.replaceChildren()
})
</script>

<template>
  <div
    class="login-globe-shell"
    :class="{ 'is-hovered': isHovered }"
    aria-hidden="true"
    @pointerenter="handlePointerEnter"
    @pointerleave="handlePointerLeave"
    @pointermove="handlePointerMove"
  >
    <div ref="mountRef" class="login-globe-stage" />
  </div>
</template>

<style scoped>
.login-globe-shell {
  width: min(100%, 460px, 42vh);
  aspect-ratio: 1;
  transform: translate3d(0, 0, 0) scale(1);
  transform-origin: center;
  transition: transform 560ms cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}

.login-globe-shell:hover,
.login-globe-shell.is-hovered {
  transform: translate3d(0, -22px, 0) scale(1.015);
}

.login-globe-stage {
  width: 100%;
  height: 100%;
}

.login-globe-stage :deep(.login-globe-canvas) {
  width: 100%;
  height: 100%;
  display: block;
  background: transparent;
  pointer-events: none;
}

@media (max-width: 1439px) {
  .login-globe-shell {
    width: min(100%, 390px, 42vh);
  }
}

@media (max-width: 1099px) {
  .login-globe-shell {
    width: min(100%, 320px, 42vh);
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-globe-shell {
    transition-duration: 220ms;
  }

  .login-globe-shell:hover,
  .login-globe-shell.is-hovered {
    transform: translate3d(0, -6px, 0);
  }
}
</style>
