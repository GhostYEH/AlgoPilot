import * as THREE from 'three'

type Position = [number, number]
type Arc = Position[]
type Ring = Position[]

type LandTopology = {
  arcs: Arc[]
  transform: {
    scale: Position
    translate: Position
  }
  objects: {
    land: {
      geometries: Array<{
        type: 'Polygon' | 'MultiPolygon'
        arcs: number[][] | number[][][]
      }>
    }
  }
}

type PreparedPolygon = {
  rings: Ring[]
  bounds: [number, number, number, number]
}

function decodeArc(topology: LandTopology, arcIndex: number): Ring {
  const index = arcIndex < 0 ? ~arcIndex : arcIndex
  const source = topology.arcs[index]
  if (!source) return []

  const [scaleX, scaleY] = topology.transform.scale
  const [translateX, translateY] = topology.transform.translate
  let x = 0
  let y = 0

  const points = source.map(([deltaX, deltaY]) => {
    x += deltaX
    y += deltaY
    return [x * scaleX + translateX, y * scaleY + translateY] as Position
  })

  return arcIndex < 0 ? points.reverse() : points
}

function stitchRing(topology: LandTopology, arcIndexes: number[]): Ring {
  const ring: Ring = []
  arcIndexes.forEach((arcIndex, index) => {
    const arc = decodeArc(topology, arcIndex)
    ring.push(...(index === 0 ? arc : arc.slice(1)))
  })
  return ring
}

function preparePolygons(topology: LandTopology): PreparedPolygon[] {
  const geometry = topology.objects.land.geometries[0]
  if (!geometry) return []

  const rawPolygons =
    geometry.type === 'Polygon'
      ? [geometry.arcs as number[][]]
      : (geometry.arcs as number[][][])

  return rawPolygons
    .map((polygonArcs) => {
      const rings = polygonArcs.map((ringArcs) => stitchRing(topology, ringArcs))
      const outer = rings[0] ?? []
      const longitudes = outer.map(([longitude]) => longitude)
      const latitudes = outer.map(([, latitude]) => latitude)

      return {
        rings,
        bounds: [
          Math.min(...longitudes),
          Math.min(...latitudes),
          Math.max(...longitudes),
          Math.max(...latitudes),
        ] as PreparedPolygon['bounds'],
      }
    })
    .filter(({ rings }) => (rings[0]?.length ?? 0) > 2)
}

function pointInRing(longitude: number, latitude: number, ring: Ring) {
  let inside = false

  for (let index = 0, previous = ring.length - 1; index < ring.length; previous = index++) {
    const [currentX, currentY] = ring[index]!
    const [previousX, previousY] = ring[previous]!
    const intersects =
      currentY > latitude !== previousY > latitude &&
      longitude <
        ((previousX - currentX) * (latitude - currentY)) / (previousY - currentY) + currentX

    if (intersects) inside = !inside
  }

  return inside
}

function pointInLand(longitude: number, latitude: number, polygons: PreparedPolygon[]) {
  return polygons.some(({ rings, bounds }) => {
    if (
      longitude < bounds[0] ||
      latitude < bounds[1] ||
      longitude > bounds[2] ||
      latitude > bounds[3]
    ) {
      return false
    }

    if (!pointInRing(longitude, latitude, rings[0]!)) return false
    return !rings.slice(1).some((hole) => pointInRing(longitude, latitude, hole))
  })
}

export function latLngToVector3(latitude: number, longitude: number, radius: number) {
  const latitudeRadians = THREE.MathUtils.degToRad(latitude)
  const longitudeRadians = THREE.MathUtils.degToRad(longitude)
  const cosLatitude = Math.cos(latitudeRadians)

  return new THREE.Vector3(
    radius * cosLatitude * Math.sin(longitudeRadians),
    radius * Math.sin(latitudeRadians),
    radius * cosLatitude * Math.cos(longitudeRadians),
  )
}

export function createLandPointPositions(topologyInput: unknown, radius = 1.018) {
  const topology = topologyInput as LandTopology
  const polygons = preparePolygons(topology)
  const positions: number[] = []
  const latitudeStep = 2.7
  const longitudeStep = 2.7

  for (let latitude = -78; latitude <= 82; latitude += latitudeStep) {
    const rowOffset = Math.round((latitude + 78) / latitudeStep) % 2 === 0 ? 0 : 1.35

    for (let longitude = -180 + rowOffset; longitude < 180; longitude += longitudeStep) {
      if (!pointInLand(longitude, latitude, polygons)) continue
      const point = latLngToVector3(latitude, longitude, radius)
      positions.push(point.x, point.y, point.z)
    }
  }

  return new Float32Array(positions)
}

export function createLatitudeLine(latitude: number, radius = 1.008, segments = 160) {
  const points: THREE.Vector3[] = []
  for (let index = 0; index <= segments; index += 1) {
    points.push(latLngToVector3(latitude, -180 + (index / segments) * 360, radius))
  }
  return points
}

export function createLongitudeLine(longitude: number, radius = 1.008, segments = 120) {
  const points: THREE.Vector3[] = []
  for (let index = 0; index <= segments; index += 1) {
    points.push(latLngToVector3(-90 + (index / segments) * 180, longitude, radius))
  }
  return points
}
