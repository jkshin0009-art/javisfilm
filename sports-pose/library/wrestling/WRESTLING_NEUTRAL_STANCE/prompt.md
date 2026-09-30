# WRESTLING_NEUTRAL_STANCE

Freestyle wrestling neutral stance: staggered feet wider than the shoulders, hips low with the knees bent about 70-75 degrees, back straight and leaning forward, head up, hands in front at knee to waist height, elbows in.

- 이름(ko): 레슬링 기본 자세, 레슬링 스탠스, 레슬링 준비 자세, 자유형 레슬링 자세
- names (en): wrestling stance, neutral stance, freestyle wrestling stance, wrestler ready position

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #WRESTLING_NEUTRAL_STANCE

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 12 deg, turned 7 deg to the athlete's left of the chest line; face pointing forward and slightly down. Eyes up on the opponent's hips and chest.
- Torso: trunk line (hips to shoulders) 45 deg forward of vertical; spine flexed 15 deg over the pelvis; shoulders square with the hips.
- Right arm: upper arm raised 45 deg from the side of the trunk, pointing down; elbow bent to about a right angle (80 deg flexion); forearm pointing forward and slightly to the athlete's left; palm facing down and slightly to the athlete's left and slightly backward; wrist neutral; hand: relaxed, fingers softly curled; fingertips 0.68 m above the floor.
- Left arm: upper arm raised 50 deg from the side of the trunk, pointing down; elbow deeply bent (70 deg flexion); forearm pointing forward and slightly down; palm facing down and slightly backward and slightly to the athlete's right; wrist neutral; hand: relaxed, fingers softly curled; fingertips 0.66 m above the floor.
- Right leg (rear leg): hip flexed 22 deg; knee bent (60 deg flexion); thigh pointing down, shin pointing backward and slightly down; ankle dorsiflexed 37 deg; on the ball of the foot, heel raised.
- Left leg (lead leg): hip flexed 75 deg, abducted 12 deg; knee deeply bent (75 deg flexion); thigh pointing forward and down, shin pointing down and slightly backward; ankle dorsiflexed 29 deg; foot flat on the floor.
- Base: ankles 56 cm apart (32% of body height, 1.4x shoulder width); every support foot touches the floor, none floats.
- Technique cue: head up, back straight
- Technique cue: elbows in, hands ready
- Technique cue: stay low, move with small steps

3. OBJECT_INTERACTION:
- Opponent about 1.5 m away in the same stance.
- Legal under the UWW rules: no fist or hand on the opponent's face.

4. CINEMATIC_CAMERA:
- front: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Opponent's view, eyes up, hands ready.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: low hips, straight back leaning forward.
- low_cinema: camera 0.5 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide frame on the mat, arena lights.

5. KINETIC_ENERGY:
- singlet stretched across the back
- sweat on the shoulders under the lights
- mat squeaking under the shoes
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a wrestler in a neutral stance, ready to shoot. Feet wider than the shoulders and staggered with the left foot forward, rear heel up; knees bent about 70-75 degrees with the hips low; back straight and leaning forward from the hips; head up with the eyes forward; hands in front between knee and waist height, elbows in close to the body. Head up, back straight. Elbows in, hands ready. Stay low, move with small steps. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Opponent's view, eyes up, hands ready. Singlet stretched across the back; sweat on the shoulders under the lights. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, loose clothing instead of a singlet, both wrestlers in the same colour, boxing gloves, street shoes, judogi, standing upright with straight legs, rounded back looking at the floor, hand choking the opponent's throat, full nelson, punching, elbow to the head, wrestler standing outside the circle
```

## Control images

- `openpose_front.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.5 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: r_leg.ankle = -37 is beyond the usual range -35..60

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_knee_flex | 60.0 | 55..110 | knees bent, hips low | EST |
| trunk_lean_fwd | 45.0 | 30..65 | back straight, leaning forward from the hips | EST |
| stance_over_shoulders | 1.4 | 1.1..2.2 | feet wider than the shoulders, staggered | EST |

## Official game rules (UWW International Wrestling Rules (freestyle and Greco-Roman))

| rule | what | check on this skeleton |
|---|---|---|
| UWW Cautions: illegal holds | Illegal holds: Choking, the full nelson, twisting fingers or other small joints, a headlock without an arm enclosed, and bending a joint beyond its range are cautions. | text only |
| UWW Cautions and disqualification: brutality | Striking, butting, biting: Striking, head butting, elbowing, biting and scratching are forbidden; slamming the opponent head first into the mat is brutality. | not measurable here ("unknown point 'B.nose'") |
| UWW Cautions: fleeing the mat or the hold | Fleeing: Stepping out of the circle to avoid wrestling, or fleeing a hold, is a caution with points to the opponent; a foot in the protection area in the standing position gives the opponent a point. | text only |

Scene rules for a full match shot (players, uniforms, officials):

- One-piece singlet, one wrestler in red and one in blue (by draw), wrestling shoes without heels, buckles or metal, laces covered; ear guards optional for seniors; a handkerchief tucked into the singlet; no jewellery; long hair covered. (UWW Wrestler's equipment)
- Circular 9 m competition surface on a square mat: dark-blue 7 m central circle with a 1 m starting circle in the middle, an orange 1 m passivity band around it, a protection area of a contrasting colour outside; red and blue corners diagonally opposite. (UWW Mat)
- Referee on the mat wearing red and blue wristbands, a judge and a mat chairman at the table; coaches seated in the red and blue corners. (UWW Officials)

Rulebook: https://uww.org/governance/rules

## Sources

- [UWW] UWW International Wrestling Rules: singlet, mat, cautions, Greco-Roman leg restrictions (secondary summaries read this session; uww.org itself not reachable) https://uww.org/governance/rules
- [EST] Estimate from standard wrestling coaching (no measured joint angle checked this session) 
