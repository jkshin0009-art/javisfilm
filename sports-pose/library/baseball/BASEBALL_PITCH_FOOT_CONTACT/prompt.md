# BASEBALL_PITCH_FOOT_CONTACT

Right-handed baseball pitcher at stride-foot contact: long stride landing slightly closed, hips opening while the shoulders stay closed, throwing arm up in the 90/90 position, glove arm pointing at the plate.

- 이름(ko): 야구 투구 착지, 스트라이드 착지, 투수 90/90 자세, 코킹 자세
- names (en): baseball pitch foot contact, stride foot plant, 90/90 arm position, arm cocking

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASEBALL_PITCH_FOOT_CONTACT

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 11 deg, turned 74 deg to the athlete's left of the chest line; face pointing to the athlete's left and slightly forward. Eyes locked on the catcher's mitt.
- Torso: trunk line (hips to shoulders) 2 deg forward of vertical, leaning 8 deg to the athlete's right; spine arched back (extended) 8 deg over the pelvis; shoulder line rotated 30 deg to the right of the hip line (hip-shoulder separation).
- Right arm (throwing arm): upper arm raised 90 deg from the side of the trunk, pointing to the athlete's right and slightly backward; elbow bent to about a right angle (95 deg flexion); forearm pointing forward and up and slightly to the athlete's right; palm facing forward and to the athlete's right and slightly down; wrist extended (cocked back) 20 deg; hand: fingers wrapped firmly around what it holds; upper arm externally rotated 70 deg (forearm laid back); fingertips 1.41 m above the floor.
- Left arm (glove arm): upper arm raised 85 deg from the side of the trunk, pointing to the athlete's left and forward; elbow bent (35 deg flexion); forearm pointing forward and slightly to the athlete's left; palm facing to the athlete's left and down and slightly backward; wrist neutral; hand: cupped, fingers slightly curled and spread; fingertips 1.13 m above the floor.
- Right leg (pivot leg on the rubber): hip flexed 6 deg, abducted 42 deg; knee bent (58 deg flexion); thigh pointing down and to the athlete's right, shin pointing backward and slightly to the athlete's right and slightly down; ankle dorsiflexed 25 deg; on the ball of the foot, heel raised.
- Left leg (stride leg): hip flexed 66 deg, abducted 25 deg; knee bent (43 deg flexion); thigh pointing forward and slightly down and slightly to the athlete's left, shin pointing down and slightly to the athlete's left; ankle plantar-flexed (toes pointed) 12 deg; foot flat on the floor.
- Base: ankles 137 cm apart (74% of body height, 3.3x shoulder width); every support foot touches the floor, none floats.
- Technique cue: stride about 80-85 % of height, landing slightly closed
- Technique cue: throwing arm up in the 90/90 position
- Technique cue: hips open while the shoulders stay closed
- Technique cue: glove arm points at the target

3. OBJECT_INTERACTION:
- ball (7 cm diameter): center 1.27 m above the floor; touching the right palm; surface 45 cm from the right shoulder (to the athlete's right and slightly up and slightly forward of it).
- Pitcher's plate (rubber) 61 x 15 cm, white, on top of a mound 25 cm above home plate; the front edge of the plate is 18.44 m from the rear point of home plate.
- Legal under the OBR rules: the pivot foot drags from the rubber, it does not hop forward and re-plant; the stride goes straight toward home plate; a dark glove, a bare pitching hand, a clean white ball.

4. CINEMATIC_CAMERA:
- catcher_view: eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher.
- first_base_side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view from the first-base side: stride and arm path read clearly.
- low_cinema: camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide cinematic frame from the grass in front of the mound, stadium lights behind.

5. KINETIC_ENERGY:
- dirt spraying from the landing foot
- jersey stretched across the chest by the hip-shoulder separation
- motion blur on the stride leg, face sharp
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed baseball pitcher landing the stride foot with the throwing arm cocked in the 90/90 position. Long stride about 83 % of body height, left foot planted slightly closed toward the third-base side of the line, left knee bent about 50 degrees; right pivot foot still on the rubber on its toes; hips opening toward the plate while the shoulders stay closed; right upper arm level with the shoulders and behind the shoulder line, elbow bent 90 degrees, forearm raised and pointing up, ball facing away from the plate; glove arm extended toward home plate. Stride about 80-85 % of height, landing slightly closed. Throwing arm up in the 90/90 position. Hips open while the shoulders stay closed. Glove arm points at the target. Eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher. Dirt spraying from the landing foot; jersey stretched across the chest by the hip-shoulder separation. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, landing on the right foot, forearm hanging down, elbow bent backwards, short shoulder-width stride, glove arm missing, both feet in the air, pitcher hopping forward and re-planting the back foot, white or grey pitcher's glove, tape or bandage on the pitching hand, bracelet on the pitching wrist
```

## Control images

- `openpose_catcher_view.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot.
- `openpose_first_base_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| stride_pct_height | 74.3 | 70..92 | stride about 83 % of height (ankle to ankle 150 +/- 15 cm); the model allows 1.5 SD below the mean | ISBS10, OBP-P |
| r_shoulder_elev | 90.0 | 80..105 | throwing shoulder abducted about 90 deg | ISBS10, OBP-P |
| r_elbow_flex | 95.0 | 80..115 | elbow flexed about 90-100 deg | ISBS10, OBP-P |
| r_arm.rot | 70.0 | 25..80 | external rotation about 30-56 deg at foot contact | ISBS10, OBP-P |
| l_knee_flex | 43.0 | 40..62 | lead knee about 45-52 deg | ISBS10, OBP-P |
| hip_shoulder_sep | -30.4 | ..-20 | hips open ahead of the closed shoulders (separation about 30 deg) | OBP-P |
| l_foot_z | 0.0 | ..0.03 | stride foot planted | CG19 |

## Official game rules (MLB Official Baseball Rules (2025 edition; values unchanged for many seasons))

| rule | what | check on this skeleton |
|---|---|---|
| OBR 5.07(a) Comment, 6.02(a)-(b) | No second step or replanted pivot foot: The pitcher may not take a second step toward home plate with either foot or reset the pivot foot during the delivery (balk with runners on, illegal pitch otherwise); the pivot foot may drag. | text only |
| OBR 6.02(a)(3), (6), (7) | Balk postures: A balk includes delivering to the batter while not facing the batter, making the pitching motion while not touching the pitcher's plate, and throwing to a base without stepping directly toward it. | text only |
| OBR 3.07, 6.02(c) | Pitcher's glove, hand and ball: The glove may not be white or grey or carry other-coloured material; nothing may be attached to the pitching hand or wrist; no foreign substance on the ball. | text only |
| OBR Definitions of Terms (strike zone) | Strike zone: Over home plate, from the hollow beneath the kneecap up to the midpoint between the top of the shoulders and the top of the uniform pants, judged from the batter's stance. | text only |
| equipment | mound_height | OK: drop_m 0.254 (official 0.251-0.257, OBR 2.01 (10 in above home plate)) |
| equipment | mound_slope | OK: slope 0.0833 (official 0.0813-0.0853, OBR 2.01 (1 in per ft)) |
| equipment | mound_flat_front | OK: top_x_m 0.152 (official 0.142-0.162, OBR 2.01 (slope starts 6 in in front of the rubber)) |
| equipment | ball_size | OK: diameter_m 0.074 (official 0.0728-0.0748, OBR 3.01 (9-9.25 in around)) |

Scene rules for a full match shot (players, uniforms, officials):

- Nine fielders per team. (OBR 1.01)
- The catcher crouches directly behind home plate in the catcher's box; the plate umpire (umpire-in-chief) stands behind the catcher; base umpires stand where they see the bases. (OBR 5.02(a), 8.03)
- All fielders except the catcher stand in fair territory; with the pitcher on the rubber, two infielders are on each side of second base with both feet on the infield dirt. (OBR 5.02(c))
- Batters, base runners and base coaches wear batting helmets (ear flap); the catcher wears a helmet and mask. (OBR 3.08)
- The pitcher's glove is not white or grey (piping excepted) and carries no other-coloured material; nothing is attached to the pitching hand, fingers or wrists (no tape, bandage or bracelet). (OBR 3.07(a), 6.02(c)(7))
- Home plate is a white five-sided slab 43 cm wide; the white pitcher's plate (61 x 15 cm) sits on a mound 25 cm above home plate, 18.44 m away. (OBR 2.02, 2.04)

Rulebook: https://mktg.mlbstatic.com/mlb/official-information/2025-official-baseball-rules.pdf

## Sources

- [OBP-P] Driveline OpenBiomechanics, baseball_pitching (100 pitchers, 411 fastballs, 1.85 +/- 0.07 m): means computed from the dataset's point-of-interest and full-signal files (CC BY-NC-SA 4.0; only summary numbers used here) https://github.com/drivelineresearch/openbiomechanics/tree/main/baseball_pitching
- [ISBS10] Fleisig, ISBS 2010 keynote: stride 83 +/- 4 % of height, lead knee 45 deg, shoulder abduction 93 deg, ER 56 deg, elbow 90 deg at foot contact https://ojs.ub.uni-konstanz.de/cpa/article/view/4377
- [CG19] A Clinician's Guide to Analysis of the Pitching Motion (2019): balance point, 90/90 arm position, MER about 170 deg https://pmc.ncbi.nlm.nih.gov/articles/PMC6542879/
- [ASMR22] Biomechanical Analysis of the Throwing Athlete, Arthrosc Sports Med Rehabil 2022: stride over 80 % of height, MER 170-180 deg https://pmc.ncbi.nlm.nih.gov/articles/PMC8811517/
