# WRESTLING_GRECO_BODY_LOCK

Greco-Roman body lock: chest to chest, the attacker's arms wrapped around the opponent's waist with the hands locked behind the back, heads side by side, hips close, the opponent's arms over the attacker's shoulders; no holds below the waist.

- 이름(ko): 그레코로만 바디락, 레슬링 몸통 잡기, 그레코로만형 클린치, 바디 락
- names (en): greco-roman body lock, wrestling body lock, bear hug clinch, greco clinch

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #WRESTLING_GRECO_BODY_LOCK

2. ANATOMICAL_BONES:
- Gaze & head: head level, turned 20 deg to the athlete's right of the chest line; face pointing forward and slightly down and slightly to the athlete's right. Head beside the opponent's head, eyes past the ear.
- Torso: trunk line (hips to shoulders) 15 deg forward of vertical; spine flexed 5 deg over the pelvis; shoulders square with the hips.
- Right arm (right arm around the waist): upper arm raised 44 deg from the side of the trunk, pointing down and slightly to the athlete's left and slightly forward; elbow bent (49 deg flexion); forearm pointing forward and slightly to the athlete's left; palm facing to the athlete's left and slightly up; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 1.01 m above the floor.
- Left arm (left arm around the waist): upper arm raised 33 deg from the side of the trunk, pointing down and slightly forward; elbow deeply bent (67 deg flexion); forearm pointing forward; palm facing to the athlete's right and down and slightly forward; wrist extended (cocked back) 30 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.08 m above the floor.
- Right leg: hip flexed 30 deg, abducted 12 deg; knee bent (35 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle dorsiflexed 13 deg; foot flat on the floor.
- Left leg: hip flexed 10 deg; knee slightly bent (28 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle dorsiflexed 26 deg; foot flat on the floor.
- Base: ankles 46 cm apart (26% of body height, 1.1x shoulder width); every support foot touches the floor, none floats.
- B (opponent in the clinch): 46 cm forward of the main athlete, facing the main athlete; trunk 15 deg forward of vertical; knees 35/28 deg (right/left); elbows 99/110 deg; both feet on the floor. Opponent in a blue singlet, arms over the attacker's shoulders, hands on the upper back, hips pushed back to defend.
- Technique cue: lock the hands above the hips, not below
- Technique cue: chest to chest, hips in
- Technique cue: lift and arch for the throw

3. OBJECT_INTERACTION:
- Legal under the UWW rules: both hands are locked above the opponent's waist; no fist or hand on the opponent's face.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view at mat level, both wrestlers in profile.
- three_quarter: eye-level shot, three-quarter front view, 35mm standard lens, full-body shot. Three-quarter view, faces and hand positions sharp.
- low_cinema: camera 0.4 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Low wide frame on the mat, orange passivity band and arena lights.

5. KINETIC_ENERGY:
- singlets straining, muscles tense
- feet pushing into the mat
- sweat glistening under the lights
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, two Greco-Roman wrestlers locked chest to chest in a body lock. Opposite the main athlete: {PARTNER_B} as the opponent in the clinch. Chest to chest with the opponent, knees bent and hips in close; both arms wrapped around the opponent's waist above the belt line with the hands locked together behind the back; heads side by side, cheek to cheek; the opponent's arms over the attacker's shoulders with the hands on the upper back. Lock the hands above the hips, not below. Chest to chest, hips in. Lift and arch for the throw. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view at mat level, both wrestlers in profile. Singlets straining, muscles tense; feet pushing into the mat. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, loose clothing instead of a singlet, both wrestlers in the same colour, boxing gloves, street shoes, judogi, hands on the opponent's legs, leg trip in Greco-Roman, hands grabbing the opponent's legs, leg trip, hand choking the opponent's throat, full nelson, punching, elbow to the head
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_three_quarter.png` / `.json`: 1152x896, eye-level shot, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.4 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 48.7 | 40.. | arms wrapped around the waist, elbows bent | EST |
| dist:r_palm:l_palm | 8.0 | ..12 | hands locked together behind the opponent's back | EST |

## Official game rules (UWW International Wrestling Rules (freestyle and Greco-Roman))

| rule | what | check on this skeleton |
|---|---|---|
| UWW Greco-Roman: holds below the waist | Greco-Roman: no holds below the waist: In Greco-Roman, attacking or holding the opponent below the waist and using the legs to trip, hook or block are forbidden; all holds are on the upper body. | OK: lowest of r_palm/l_palm +10 cm against the B.belt back |
| UWW Cautions: illegal holds | Illegal holds: Choking, the full nelson, twisting fingers or other small joints, a headlock without an arm enclosed, and bending a joint beyond its range are cautions. | text only |
| UWW Cautions and disqualification: brutality | Striking, butting, biting: Striking, head butting, elbowing, biting and scratching are forbidden; slamming the opponent head first into the mat is brutality. | OK: l knuckles 52 cm from B.chin |

Scene rules for a full match shot (players, uniforms, officials):

- One-piece singlet, one wrestler in red and one in blue (by draw), wrestling shoes without heels, buckles or metal, laces covered; ear guards optional for seniors; a handkerchief tucked into the singlet; no jewellery; long hair covered. (UWW Wrestler's equipment)
- Circular 9 m competition surface on a square mat: dark-blue 7 m central circle with a 1 m starting circle in the middle, an orange 1 m passivity band around it, a protection area of a contrasting colour outside; red and blue corners diagonally opposite. (UWW Mat)
- Referee on the mat wearing red and blue wristbands, a judge and a mat chairman at the table; coaches seated in the red and blue corners. (UWW Officials)

Rulebook: https://uww.org/governance/rules

## Sources

- [UWW] UWW International Wrestling Rules: singlet, mat, cautions, Greco-Roman leg restrictions (secondary summaries read this session; uww.org itself not reachable) https://uww.org/governance/rules
- [EST] Estimate from standard wrestling coaching (no measured joint angle checked this session) 
