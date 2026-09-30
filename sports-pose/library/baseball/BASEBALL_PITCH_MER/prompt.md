# BASEBALL_PITCH_MER

Right-handed baseball pitcher at maximum shoulder external rotation: chest square to the plate, throwing forearm laid back behind the head with the elbow at 90 degrees, front leg braced, trunk tilting to the glove side.

- 이름(ko): 야구 투구 최대 외회전, 레이백, 팔 뒤로 젖힘, 투구 가속 직전
- names (en): baseball pitch max external rotation, layback, MER, arm lay back

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASEBALL_PITCH_MER

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward and slightly down. Eyes on the target.
- Torso: trunk line (hips to shoulders) 18 deg forward of vertical, leaning 25 deg to the athlete's left; spine flexed 6 deg over the pelvis; shoulder line rotated 10 deg to the left of the hip line (hip-shoulder separation).
- Right arm (throwing arm): upper arm raised 90 deg from the side of the trunk, pointing to the athlete's right and slightly up; elbow bent to about a right angle (92 deg flexion); forearm pointing backward and slightly up; palm facing up; wrist extended (cocked back) 30 deg; hand: fingers wrapped firmly around what it holds; upper arm externally rotated 168 deg (forearm laid back); fingertips 1.36 m above the floor.
- Left arm (glove arm): upper arm raised 36 deg from the side of the trunk, pointing down; elbow bent to about a right angle (95 deg flexion); forearm pointing forward and slightly to the athlete's right and slightly up; palm facing to the athlete's right and down; wrist neutral; hand: cupped, fingers slightly curled and spread; fingertips 0.77 m above the floor.
- Right leg (pivot leg on the rubber): hip extended 31 deg; knee bent (39 deg flexion); thigh pointing down and backward and slightly to the athlete's left, shin pointing backward; ankle neutral; on the ball of the foot, heel raised.
- Left leg (stride leg): hip flexed 74 deg; knee bent (50 deg flexion); thigh pointing forward and slightly down and slightly to the athlete's right, shin pointing down and slightly to the athlete's right; ankle plantar-flexed (toes pointed) 13 deg; foot flat on the floor.
- Base: ankles 120 cm apart (65% of body height, 2.9x shoulder width); every support foot touches the floor, none floats.
- Technique cue: chest faces the plate while the forearm lays back
- Technique cue: front leg braces
- Technique cue: elbow stays at about 90 degrees

3. OBJECT_INTERACTION:
- ball (7 cm diameter): center 1.43 m above the floor; touching the right palm; surface 46 cm from the right shoulder (to the athlete's right and up and slightly backward of it).
- Pitcher's plate (rubber) 61 x 15 cm, white, on top of a mound 25 cm above home plate; the front edge of the plate is 18.44 m from the rear point of home plate.
- Legal under the OBR rules: the pivot foot drags from the rubber, it does not hop forward and re-plant; the stride goes straight toward home plate; a dark glove, a bare pitching hand, a clean white ball.

4. CINEMATIC_CAMERA:
- catcher_view: eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher.
- first_base_side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view from the first-base side: stride and arm path read clearly.
- low_cinema: camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide cinematic frame from the grass in front of the mound, stadium lights behind.

5. KINETIC_ENERGY:
- extreme motion blur on the forearm and ball
- jersey sleeve rippling
- dirt kicking up behind the dragging foot
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed baseball pitcher at maximum layback of the throwing arm, just before accelerating the ball. Chest square to home plate; trunk leaning forward and tilted toward the glove side; right upper arm level with the shoulders, elbow bent 90 degrees and above the shoulder line, forearm laid back behind the head nearly horizontal and pointing toward second base, ball behind the head; glove tucked in front of the chest; left front leg planted and braced, knee bent about 45 degrees; right foot dragging on its toes behind. Chest faces the plate while the forearm lays back. Front leg braces. Elbow stays at about 90 degrees. Eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher. Extreme motion blur on the forearm and ball; jersey sleeve rippling. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, elbow bent backwards, broken-looking arm, ball floating behind the head, an extra arm, upright trunk, pitcher hopping forward and re-planting the back foot, white or grey pitcher's glove, tape or bandage on the pitching hand, bracelet on the pitching wrist
```

## Control images

- `openpose_catcher_view.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot.
- `openpose_first_base_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: r_arm.rot = 168 is beyond the usual range -70..120
- warn: r_leg.flex = -31 is beyond the usual range -30..125

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_arm.rot | 168.0 | 150..185 | maximum external rotation about 169 deg (range 143-192) | OBP-P, CG19, ASMR22 |
| r_shoulder_elev | 90.0 | 80..100 | shoulder abduction about 90 deg | OBP-P |
| r_elbow_flex | 92.0 | 80..105 | elbow about 92 deg, not bent backwards | OBP-P |
| trunk_lean_right | -25.1 | ..-12 | trunk tilts toward the glove side (about 24 deg) | OBP-P |
| l_knee_flex | 50.4 | 35..60 | front knee braced at about 47 deg | OBP-P |
| l_foot_z | -0.0 | ..0.03 | stride foot planted | OBP-P |

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
- [CG19] A Clinician's Guide to Analysis of the Pitching Motion (2019): balance point, 90/90 arm position, MER about 170 deg https://pmc.ncbi.nlm.nih.gov/articles/PMC6542879/
- [ASMR22] Biomechanical Analysis of the Throwing Athlete, Arthrosc Sports Med Rehabil 2022: stride over 80 % of height, MER 170-180 deg https://pmc.ncbi.nlm.nih.gov/articles/PMC8811517/
- [DIL93] Dillman, Fleisig & Andrews 1993, JOSPT: biomechanics of pitching https://www.jospt.org/doi/10.2519/jospt.1993.18.2.402
