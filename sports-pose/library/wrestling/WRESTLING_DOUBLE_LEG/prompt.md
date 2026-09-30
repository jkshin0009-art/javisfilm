# WRESTLING_DOUBLE_LEG

Freestyle double-leg takedown at the penetration step: attacker's right knee on the mat between the opponent's feet, left leg driving back on the toes, head up on the opponent's side, chest against the thighs, both arms wrapped behind the opponent's knees.

- 이름(ko): 레슬링 양다리 태클, 더블렉 태클, 레슬링 태클, 양발 태클
- names (en): wrestling double leg takedown, double leg shot, penetration step, wrestling tackle

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #WRESTLING_DOUBLE_LEG

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 50 deg; face pointing forward and slightly down. Head up, eyes forward past the opponent's hip.
- Torso: trunk line (hips to shoulders) 65 deg forward of vertical; spine flexed 15 deg over the pelvis; shoulders square with the hips.
- Right arm: upper arm raised 89 deg from the side of the trunk, pointing down and to the athlete's left and slightly forward; elbow deeply bent (75 deg flexion); forearm pointing forward; palm facing to the athlete's left and slightly up; wrist extended (cocked back) 5 deg; hand: cupped, fingers slightly curled and spread; fingertips 0.47 m above the floor.
- Left arm: upper arm raised 87 deg from the side of the trunk, pointing down and slightly to the athlete's left and slightly forward; elbow bent to about a right angle (83 deg flexion); forearm pointing forward and slightly up; palm facing down and slightly forward; wrist extended (cocked back) 7 deg; hand: cupped, fingers slightly curled and spread; fingertips 0.53 m above the floor.
- Right leg (penetrating knee): hip flexed 75 deg; knee fully folded (120 deg flexion); thigh pointing down and slightly forward, shin pointing backward; ankle plantar-flexed (toes pointed) 65 deg; foot 5 cm above the floor.
- Left leg (drive leg): hip extended 14 deg; knee slightly bent (22 deg flexion); thigh pointing backward and slightly down, shin pointing backward; ankle dorsiflexed 25 deg; on the ball of the foot, heel raised.
- On the mat/floor: right shin front, left foot rest on the surface.
- B (opponent being taken down): 81 cm forward and slightly to the athlete's left of the main athlete, facing the main athlete; trunk 30 deg forward of vertical; knees 20/20 deg (right/left); elbows 70/70 deg; both feet on the floor. Opponent in a blue singlet caught upright, hands reaching down too late to sprawl.
- Technique cue: level change before you shoot
- Technique cue: head up, back straight
- Technique cue: drive through, lift or turn the corner

3. OBJECT_INTERACTION:
- Legal under the UWW rules: the hands are wrapped behind the opponent's legs (legal in freestyle only); no fist or hand on the opponent's face.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view at mat level, both wrestlers in profile.
- three_quarter: eye-level shot, three-quarter front view, 35mm standard lens, full-body shot. Three-quarter view, faces and hand positions sharp.
- low_cinema: camera 0.4 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Low wide frame on the mat, orange passivity band and arena lights.

5. KINETIC_ENERGY:
- opponent's knees buckling
- mat shoe squeak and dust
- sweat flying off the heads
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a wrestler shooting a double-leg takedown. Opposite the main athlete: {PARTNER_B} as the opponent being taken down. Right knee dropped to the mat between the opponent's feet, left leg driving back with the toes on the mat; hips low and forward; back straight, head up and pressed against the opponent's side; chest against the opponent's thighs; both arms wrapped around the backs of the opponent's knees, hands cupped. Level change before you shoot. Head up, back straight. Drive through, lift or turn the corner. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view at mat level, both wrestlers in profile. Opponent's knees buckling; mat shoe squeak and dust. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, loose clothing instead of a singlet, both wrestlers in the same colour, boxing gloves, street shoes, judogi, head down looking at the mat, hands grabbing the opponent's ankles, hand choking the opponent's throat, full nelson, punching, elbow to the head, wrestler standing outside the circle
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_three_quarter.png` / `.json`: 1152x896, eye-level shot, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.4 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: r_leg.ankle = 65 is beyond the usual range -35..60

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_knee_flex | 120.0 | 70.. | penetration step: lead knee bent and dropped to the mat | EST |
| z:r_shin_front | 0.0 | ..0.04 | lead knee down on the mat between the opponent's feet | EST |

## Official game rules (UWW International Wrestling Rules (freestyle and Greco-Roman))

| rule | what | check on this skeleton |
|---|---|---|
| UWW Freestyle: legs may be attacked | Freestyle leg attacks are legal: In freestyle, grabbing the legs and tripping are allowed; a double-leg takedown is a standard legal attack. | OK: r palm 0 cm from B.l knee back |
| UWW Cautions: illegal holds | Illegal holds: Choking, the full nelson, twisting fingers or other small joints, a headlock without an arm enclosed, and bending a joint beyond its range are cautions. | text only |
| UWW Cautions and disqualification: brutality | Striking, butting, biting: Striking, head butting, elbowing, biting and scratching are forbidden; slamming the opponent head first into the mat is brutality. | OK: l knuckles 98 cm from B.chin |
| UWW Cautions: fleeing the mat or the hold | Fleeing: Stepping out of the circle to avoid wrestling, or fleeing a hold, is a caution with points to the opponent; a foot in the protection area in the standing position gives the opponent a point. | text only |

Scene rules for a full match shot (players, uniforms, officials):

- One-piece singlet, one wrestler in red and one in blue (by draw), wrestling shoes without heels, buckles or metal, laces covered; ear guards optional for seniors; a handkerchief tucked into the singlet; no jewellery; long hair covered. (UWW Wrestler's equipment)
- Circular 9 m competition surface on a square mat: dark-blue 7 m central circle with a 1 m starting circle in the middle, an orange 1 m passivity band around it, a protection area of a contrasting colour outside; red and blue corners diagonally opposite. (UWW Mat)
- Referee on the mat wearing red and blue wristbands, a judge and a mat chairman at the table; coaches seated in the red and blue corners. (UWW Officials)

Rulebook: https://uww.org/governance/rules

## Sources

- [UWW] UWW International Wrestling Rules: singlet, mat, cautions, Greco-Roman leg restrictions (secondary summaries read this session; uww.org itself not reachable) https://uww.org/governance/rules
- [EST] Estimate from standard wrestling coaching (no measured joint angle checked this session) 
