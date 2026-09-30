# BASKETBALL_DEFENSIVE_STANCE

Basketball on-ball defensive stance: feet wider than the shoulders and flat, knees bent, hips back, one hand low toward the ball, the other up at shoulder height.

- 이름(ko): 농구 수비 자세, 디펜스 스탠스, 대인 수비 자세, 낮은 수비 자세
- names (en): basketball defensive stance, on-ball defense, defensive slide stance, guarding the dribbler

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASKETBALL_DEFENSIVE_STANCE

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward and slightly down. Eyes on the ball handler's midsection.
- Torso: trunk line (hips to shoulders) 30 deg forward of vertical; shoulders square with the hips.
- Right arm (high hand, passing lane): upper arm raised 75 deg from the side of the trunk, pointing to the athlete's right and slightly down and slightly forward; elbow bent (60 deg flexion); forearm pointing forward and slightly to the athlete's right and slightly up; palm facing to the athlete's left and forward; wrist extended (cocked back) 10 deg; hand: open with fingers spread; fingertips 1.31 m above the floor.
- Left arm (low hand toward the ball): upper arm raised 45 deg from the side of the trunk, pointing down and slightly to the athlete's left; elbow slightly bent (20 deg flexion); forearm pointing down and slightly forward; palm facing forward and to the athlete's right; wrist extended (cocked back) 10 deg; hand: open with fingers spread; fingertips 0.58 m above the floor.
- Right leg: hip flexed 62 deg, abducted 26 deg; knee bent (60 deg flexion); thigh pointing down and slightly forward and slightly to the athlete's right, shin pointing down and slightly backward; ankle dorsiflexed 22 deg; foot flat on the floor.
- Left leg: hip flexed 62 deg, abducted 26 deg; knee bent (60 deg flexion); thigh pointing down and slightly forward and slightly to the athlete's left, shin pointing down and slightly backward; ankle dorsiflexed 22 deg; foot flat on the floor.
- Base: ankles 71 cm apart (38% of body height, 1.7x shoulder width); every support foot touches the floor, none floats.
- Technique cue: wide base, weight on the balls of the feet with heels down
- Technique cue: hips back, back straight
- Technique cue: one hand low to the ball, one hand up to the passing lane
- Technique cue: chest square to the ball handler

3. OBJECT_INTERACTION:
- Ball handler about 1.4 m in front at arm's length plus a step.
- Legal under the FIBA rules: the defender faces the ball handler with both feet on the floor (legal guarding position); no body contact with an opponent outside the player's own cylinder; jersey tucked into the shorts.

4. CINEMATIC_CAMERA:
- front: eye-level shot, from the front (target side), 50mm standard lens, full-body shot. From the ball handler's view: a wide, low defender.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: hips back, nose behind the toes, heels down.
- low_wide: camera 0.3 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide angle from the floor, court lines converging.

5. KINETIC_ENERGY:
- sneakers squeaking, slight lateral motion blur at the feet
- sweat on the forehead, intense focus
- jersey hanging forward
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a basketball defender in a low on-ball defensive stance guarding a dribbler. Feet about 1.5-2 times shoulder width, flat on the floor and pointing forward; knees bent about 60 degrees, hips back behind the heels, back straight and tilted slightly forward, nose behind the toes; left hand low and forward toward the ball, palm up; right hand up at shoulder height, palm facing the passing lane; head up. Wide base, weight on the balls of the feet with heels down. Hips back, back straight. One hand low to the ball, one hand up to the passing lane. Chest square to the ball handler. Eye-level shot, from the front (target side), 50mm standard lens, full-body shot. From the ball handler's view: a wide, low defender. Sneakers squeaking, slight lateral motion blur at the feet; sweat on the forehead, intense focus. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, bending at the waist with straight legs, knees collapsing inward, feet together or crossed, heels raised high, both arms straight out like a zombie, head down, defender turned sideways reaching in, defender with one foot off the floor, untucked jersey, headband wider than 10 cm
```

## Control images

- `openpose_front.png` / `.json`: 1152x896, eye-level shot, from the front (target side), 50mm standard lens, full-body shot.
- `openpose_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_wide.png` / `.json`: 1344x768, camera 0.3 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| stance_over_shoulders | 1.7 | 1.3..2.2 | feet wider than the shoulders (fastest response at about twice shoulder width) | S1, S2 |
| r_knee_flex | 60.0 | 30..75 | knees bent 30-60 deg (knee angle 120-150 deg gave the fastest response) | S1 |
| trunk_lean_fwd | 30.0 | 15..40 | back slightly forward, not bent at the waist | S2 |
| r_foot_z | 0.0 | ..0.03 | heels down, feet flat | S3 |
| l_foot_z | 0.0 | ..0.03 | heels down, feet flat | S3 |
| l_hand_z | 0.6 | ..1.0 | hand nearest the dribbler low | S4 |
| r_hand_z | 1.3 | 1.1.. | other hand at shoulder height to the passing lane | S4 |

## Official game rules (FIBA Official Basketball Rules 2024 and FIBA Basketball Equipment (OBR 2026 takes effect on 1 October 2026: free line colours, visible-sock rule removed, unsportsmanlike foul renamed; article numbers may move))

| rule | what | check on this skeleton |
|---|---|---|
| FIBA Art. 33.3 | Legal guarding position: A defender has a legal guarding position when facing the opponent with both feet on the floor; the position extends vertically (cylinder), and the defender may move sideways or backwards to keep it. | OK: chest turned 10 deg from the ball handler; feet on the floor |
| FIBA Art. 33.1, 33.2 | Cylinder and verticality: Each player owns the vertical space above their position; a player who leaves their cylinder and makes contact is responsible for it. | text only |
| FIBA Art. 4.3, 4.4 | Uniform: Shirts tucked in; sleeves, headbands, wristbands and tape of one solid team colour. | text only |

Scene rules for a full match shot (players, uniforms, officials):

- Five players per team on the court. (FIBA Art. 4.2.2)
- Home team in light (preferably white) shirts, visiting team in dark shirts; shirts tucked into the shorts; all sleeves, headbands, wristbands and tape on a team in the same solid colour, headbands at most 10 cm wide. (FIBA Art. 4.3)
- Shirt numbers only 0, 00 or 1-99: at least 20 cm tall on the back and 10 cm on the front. (FIBA Art. 4.3.2)
- A crew chief and one or two umpires in grey officials' shirts on the court; scorer, timer and shot-clock operator at the table. (FIBA Art. 45)
- Shot clocks mounted above and behind each backboard (red digits); backboard 1.80 x 1.05 m with its lower edge 2.90 m up, 1.20 m in from the endline; ring 3.05 m high with a 40-45 cm net. (FIBA Equipment)
- Court 28 x 15 m with 5 cm lines, three-point arc 6.75 m (6.60 m in the corners), free-throw line 5.80 m from the endline, no-charge semi-circle 1.25 m under the basket. (FIBA Art. 2.4)

Rulebook: https://refereeing.fiba.basketball/en/rules

## Sources

- [S1] Stirn, Dolinar & Erculj 2016, IJPAS 16:53: stance width twice shoulder width and knee angle 120-150 deg gave the quickest response https://ideas.repec.org/a/taf/rpanxx/v16y2016i1p53-63.html
- [S2] FIBA WABC Level 1 manual 1.1.1: feet about shoulder-width, knees bent, back slightly forward, nose behind the toes https://wabc.fiba.com/manual/level-1/l1-player/l1-1-defensive-basketball-skills/1-1-defensive-footwork/1-1-1-basic-defensive-footwork/
- [S3] Breakthrough Basketball: stance slightly wider than shoulders, hips back, heels down https://www.breakthroughbasketball.com/defense/stance
- [S4] FIBA WABC 1.2.1: hand nearest the dribbler low, other hand at shoulder height https://wabc.fiba.com/manual/level-1/l1-player/l1-1-defensive-basketball-skills/1-2-individual-defensive-movement-position/1-2-1-defending-player-with-the-ball/
