import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html, Line, OrbitControls } from "@react-three/drei";
import * as THREE from "three";

// The armillary sphere of SS Ch.13 v.3-16, drawn from the parametric model
// /calc/instruments/sphere returns. Every hoop and point arrives in the
// equatorial frame (z to the north pole, x to the vernal equinox); the
// scene maps that frame onto the observer's horizon once, for the moment
// asked, and the sky's revolution (v.16-20) is then a rotation of one group
// about its own z-axis — no refetch while it turns.

export interface SphereHoopData {
  key: string;
  name: string;
  kind: "great" | "solar_diurnal" | "star_diurnal" | "horizon";
  group: HoopGroup;
  normal: number[];
  offset: number;
  radius: number;
  declination: number | null;
  day_radius: number | null;
  marker: number[] | null;
  cased_below: boolean;
  note: string;
  verse: string;
}

export interface SpherePointData {
  key: string;
  name: string;
  tropical_longitude: number;
  sidereal_longitude: number;
  right_ascension: number;
  declination: number;
  vector: number[];
  note: string;
  verse: string;
}

export interface SphereData {
  latitude: number;
  longitude: number;
  lst_deg: number;
  zenith: number[];
  hoops: SphereHoopData[];
  cardinal_points: SpherePointData[];
  sign_points: SpherePointData[];
  points: SpherePointData[];
}

export type HoopGroup = "great_circles" | "solar" | "junction_stars" | "fixed_stars" | "horizon";

export const HOOP_GROUPS: { key: HoopGroup; label: string; color: string }[] = [
  { key: "great_circles", label: "Equator, colures, ecliptic", color: "#8a6d1f" },
  { key: "solar", label: "Sun's diurnal hoops", color: "#d35400" },
  { key: "junction_stars", label: "Junction stars", color: "#2471a3" },
  { key: "fixed_stars", label: "Other fixed stars", color: "#7d3c98" },
  { key: "horizon", label: "Horizon & casing", color: "#1e8449" },
];

const GROUP_COLOR = Object.fromEntries(HOOP_GROUPS.map((g) => [g.key, g.color])) as Record<
  HoopGroup,
  string
>;

const HOOP_COLOR: Record<string, string> = {
  equator: "#c0392b",
  ecliptic: "#b8860b",
  equinoctial_colure: "#7f8c8d",
  solstitial_colure: "#7f8c8d",
};

const SEGMENTS = 128;

/** Points around a circle on the unit sphere with the given normal and offset. */
function circlePoints(normal: number[], offset: number, radius: number): THREE.Vector3[] {
  const n = new THREE.Vector3(normal[0], normal[1], normal[2]).normalize();
  const helper = Math.abs(n.z) < 0.9 ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(1, 0, 0);
  const u = new THREE.Vector3().crossVectors(n, helper).normalize();
  const w = new THREE.Vector3().crossVectors(n, u).normalize();
  const centre = n.clone().multiplyScalar(offset);
  const pts: THREE.Vector3[] = [];
  for (let i = 0; i <= SEGMENTS; i++) {
    const t = (i / SEGMENTS) * Math.PI * 2;
    pts.push(
      centre
        .clone()
        .add(u.clone().multiplyScalar(radius * Math.cos(t)))
        .add(w.clone().multiplyScalar(radius * Math.sin(t))),
    );
  }
  return pts;
}

/**
 * Matrix taking equatorial-frame vectors to the scene frame at the chosen
 * moment: x to the east, y to the zenith, z to the south (toward the viewer).
 * Rows are the east, zenith and minus-north unit vectors, which form a proper
 * rotation, so nothing is mirrored.
 */
function observerMatrix(latitude: number, lstDeg: number): THREE.Matrix4 {
  const phi = THREE.MathUtils.degToRad(latitude);
  const t = THREE.MathUtils.degToRad(lstDeg);
  const east = [-Math.sin(t), Math.cos(t), 0];
  const zenith = [Math.cos(phi) * Math.cos(t), Math.cos(phi) * Math.sin(t), Math.sin(phi)];
  const north = [-Math.sin(phi) * Math.cos(t), -Math.sin(phi) * Math.sin(t), Math.cos(phi)];
  const m = new THREE.Matrix4();
  m.set(
    east[0], east[1], east[2], 0,
    zenith[0], zenith[1], zenith[2], 0,
    -north[0], -north[1], -north[2], 0,
    0, 0, 0, 1,
  );
  return m;
}

function Label({
  position,
  text,
  color,
  dy = 0,
}: {
  position: THREE.Vector3 | number[];
  text: string;
  color: string;
  /** Vertical nudge in pixels, so labels of points close together don't overprint. */
  dy?: number;
}) {
  return (
    <Html position={position as [number, number, number]} center zIndexRange={[10, 0]}>
      <span className="sphere-label" style={{ color, display: "inline-block", transform: `translateY(${dy}px)` }}>
        {text}
      </span>
    </Html>
  );
}

// The Sun sits close to the meridian point around noon and to the lagna near
// sunrise, so their labels are pushed to opposite sides of their markers.
const POINT_LABEL_DY: Record<string, number> = { sun: -16, madhya_lagna: 14, lagna: 14, asta_lagna: 14 };

function Sky({
  sphere,
  visible,
  turnRef,
  playing,
  speed,
  onTurn,
  showPoints,
}: {
  sphere: SphereData;
  visible: Set<HoopGroup>;
  turnRef: React.MutableRefObject<number>;
  playing: boolean;
  speed: number;
  onTurn: (degrees: number) => void;
  showPoints: boolean;
}) {
  const skyRef = useRef<THREE.Group>(null);
  const lastReport = useRef(0);
  const [hovered, setHovered] = useState<SphereHoopData | null>(null);

  const matrix = useMemo(() => observerMatrix(sphere.latitude, sphere.lst_deg), [sphere]);
  const hoops = useMemo(
    () =>
      sphere.hoops
        .filter((h) => h.kind !== "horizon")
        .map((h) => ({ hoop: h, points: circlePoints(h.normal, h.offset, h.radius) })),
    [sphere],
  );

  // Turning the sky westward with time: in the equatorial frame that is a
  // rotation by minus the elapsed sidereal angle about the Meru axis.
  useFrame((_, dt) => {
    if (playing) {
      turnRef.current = (turnRef.current + speed * dt) % 360;
      const now = performance.now();
      if (now - lastReport.current > 120) {
        lastReport.current = now;
        onTurn(turnRef.current);
      }
    }
    if (skyRef.current) skyRef.current.rotation.z = -THREE.MathUtils.degToRad(turnRef.current);
  });

  return (
    <group matrixAutoUpdate={false} matrix={matrix}>
      <group ref={skyRef}>
        {/* Meru staff through the earth, protruding at both poles (v.4). */}
        <Line points={[[0, 0, -1.25], [0, 0, 1.25]]} color="#5d4037" lineWidth={3} />
        <Label position={[0, 0, 1.32]} text="Meru (N)" color="#5d4037" />

        {hoops.map(({ hoop, points }) =>
          visible.has(hoop.group) ? (
            <Line
              key={hoop.key}
              points={points}
              color={HOOP_COLOR[hoop.key] ?? GROUP_COLOR[hoop.group]}
              lineWidth={hoop.kind === "great" ? 2.2 : hoop.kind === "solar_diurnal" ? 1.6 : 0.9}
              transparent
              opacity={hoop.kind === "star_diurnal" ? 0.55 : 1}
              onPointerOver={(e) => {
                e.stopPropagation();
                setHovered(hoop);
              }}
              onPointerOut={() => setHovered(null)}
            />
          ) : null,
        )}

        {hoops.map(({ hoop }) =>
          visible.has(hoop.group) && hoop.marker ? (
            <mesh
              key={`${hoop.key}-marker`}
              position={hoop.marker as [number, number, number]}
              onPointerOver={(e) => {
                e.stopPropagation();
                setHovered(hoop);
              }}
              onPointerOut={() => setHovered(null)}
            >
              <sphereGeometry args={[0.018, 10, 10]} />
              <meshBasicMaterial color={GROUP_COLOR[hoop.group]} />
            </mesh>
          ) : null,
        )}

        {visible.has("great_circles") &&
          sphere.cardinal_points.map((p) => (
            <Label key={p.key} position={p.vector} text={p.name} color="#8a6d1f" />
          ))}

        {showPoints &&
          sphere.points.map((p) =>
            p.key === "sun" ? (
              <group key={p.key}>
                <mesh position={p.vector as [number, number, number]}>
                  <sphereGeometry args={[0.045, 16, 16]} />
                  <meshBasicMaterial color="#f1c40f" />
                </mesh>
                <Label position={p.vector} text="Sun" color="#b7950b" dy={POINT_LABEL_DY.sun} />
              </group>
            ) : (
              <group key={p.key}>
                <mesh position={p.vector as [number, number, number]}>
                  <sphereGeometry args={[0.025, 12, 12]} />
                  <meshBasicMaterial color="#c0392b" />
                </mesh>
                <Label position={p.vector} text={p.name.split(" (")[0]} color="#c0392b" dy={POINT_LABEL_DY[p.key] ?? 0} />
              </group>
            ),
          )}

        {hovered && (
          <Label
            position={hovered.marker ?? circlePoints(hovered.normal, hovered.offset, hovered.radius)[0]}
            text={`${hovered.name}${hovered.declination !== null ? ` · δ ${hovered.declination.toFixed(2)}°` : ""}`}
            color="#222"
          />
        )}
      </group>
    </group>
  );
}

function Ground({ visible }: { visible: boolean }) {
  // The horizon is fixed to the observer, so it lives outside the turning sky:
  // a ring in the scene's x-z plane, with the half below cased in cloth (v.16).
  const ring = useMemo(() => circlePoints([0, 1, 0], 0, 1), []);
  if (!visible) return null;
  return (
    <group>
      <Line points={ring} color={GROUP_COLOR.horizon} lineWidth={2.4} />
      <mesh>
        <sphereGeometry args={[0.995, 48, 24, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2]} />
        <meshStandardMaterial
          color="#c8b99a"
          transparent
          opacity={0.28}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
      <Label position={[0, 0, -1.12]} text="N" color={GROUP_COLOR.horizon} />
      <Label position={[1.12, 0, 0]} text="E" color={GROUP_COLOR.horizon} />
      <Label position={[0, 0, 1.12]} text="S" color={GROUP_COLOR.horizon} />
      <Label position={[-1.12, 0, 0]} text="W" color={GROUP_COLOR.horizon} />
    </group>
  );
}

/** True when the browser can create a WebGL context at all. */
export function webglAvailable(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

export function ArmillarySphere3D({
  sphere,
  visible,
  playing,
  speed,
  turn,
  onTurn,
  showPoints,
}: {
  sphere: SphereData;
  visible: Set<HoopGroup>;
  playing: boolean;
  speed: number;
  turn: number;
  onTurn: (degrees: number) => void;
  showPoints: boolean;
}) {
  const turnRef = useRef(turn);

  // The slider drives the angle while paused; while playing the frame loop
  // owns it and reports back, so only sync from props when not playing.
  useEffect(() => {
    if (!playing) turnRef.current = turn;
  }, [turn, playing]);

  return (
    <div className="sphere-canvas">
      <Canvas camera={{ position: [2.3, 1.3, 2.6], fov: 42 }} dpr={[1, 2]}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[3, 5, 4]} intensity={0.9} />

        {/* The wooden earth-globe at the centre (v.3). */}
        <mesh>
          <sphereGeometry args={[0.16, 32, 32]} />
          <meshStandardMaterial color="#8d6e63" roughness={0.9} />
        </mesh>

        <Sky
          sphere={sphere}
          visible={visible}
          turnRef={turnRef}
          playing={playing}
          speed={speed}
          onTurn={onTurn}
          showPoints={showPoints}
        />
        <Ground visible={visible.has("horizon")} />
        <OrbitControls enablePan={false} minDistance={1.6} maxDistance={6} />
      </Canvas>
    </div>
  );
}
