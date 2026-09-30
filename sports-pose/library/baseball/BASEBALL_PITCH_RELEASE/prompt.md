# BASEBALL_PITCH_RELEASE

Right-handed baseball pitcher at ball release: trunk flexed forward and tilted to the glove side, throwing arm almost straight out in front of the stride foot, front knee firm, back foot dragging.

- 이름(ko): 야구 투구 릴리스, 공 놓는 순간, 투구 릴리스 포인트, 강속구 투구
- names (en): baseball pitch release, ball release, release point, fastball release

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASEBALL_PITCH_RELEASE

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 7 deg, turned 14 deg to the athlete's right of the chest line; face pointing forward and slightly down. Eyes on the catcher's mitt.
- Torso: trunk line (hips to shoulders) 30 deg forward of vertical, leaning 19 deg to the athlete's left; spine flexed 14 deg over the pelvis; shoulder line rotated 19 deg to the left of the hip line (hip-shoulder separation).
- Right arm (throwing arm): upper arm raised 91 deg from the side of the trunk, pointing to the athlete's right; elbow bent (32 deg flexion); forearm pointing to the athlete's right and slightly up and slightly forward; palm facing down and forward; wrist flexed 10 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.42 m above the floor.
- Left arm (glove arm): upper arm raised 40 deg from the side of the trunk, pointing down and slightly to the athlete's left; elbow bent to about a right angle (100 deg flexion); forearm pointing forward and slightly to the athlete's right; palm facing down and slightly to the athlete's right; wrist neutral; hand: cupped, fingers slightly curled and spread; fingertips 0.77 m above the floor.
- Right leg (pivot leg on the rubber): hip extended 4 deg; knee bent (54 deg flexion); thigh pointing down and slightly to the athlete's left and slightly backward, shin pointing backward; ankle neutral; on the ball of the foot, heel raised.
- Left leg (stride leg): hip flexed 65 deg; knee bent (42 deg flexion); thigh pointing forward and down and slightly to the athlete's right, shin pointing down and slightly to the athlete's right; ankle neutral; foot flat on the floor.
- Base: ankles 100 cm apart (54% of body height, 2.4x shoulder width); every support foot touches the floor, none floats.
- Technique cue: release out in front of the stride foot
- Technique cue: trunk flexes forward and tilts to the glove side
- Technique cue: front knee firm

3. OBJECT_INTERACTION:
- ball (7 cm diameter): center 1.31 m above the floor; touching the right palm; surface 139 cm from the left ankle (up and slightly to the athlete's right of it).
- Pitcher's plate (rubber) 61 x 15 cm, white, on top of a mound 25 cm above home plate; the front edge of the plate is 18.44 m from the rear point of home plate.
- Legal under the OBR rules: the pivot foot drags from the rubber, it does not hop forward and re-plant; the stride goes straight toward home plate; a dark glove, a bare pitching hand, a clean white ball.

4. CINEMATIC_CAMERA:
- catcher_view: eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher.
- first_base_side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view from the first-base side: stride and arm path read clearly.
- low_cinema: camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide cinematic frame from the grass in front of the mound, stadium lights behind.

5. KINETIC_ENERGY:
- ball leaving the fingertips with a white motion streak
- cap and jersey whipping forward
- dust cloud from the dragging back foot
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed baseball pitcher releasing a fastball. Trunk flexed forward about 35 degrees and tilted toward the glove side; throwing arm nearly straight and out in front, hand at about eye level just in front of the stride foot, fingers behind the ball; glove pulled in to the chest; left front leg planted and firm; right leg trailing behind, foot dragging on its toes. Release out in front of the stride foot. Trunk flexes forward and tilts to the glove side. Front knee firm. Eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher. Ball leaving the fingertips with a white motion streak; cap and jersey whipping forward. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, elbow bent backwards, ball stuck to the palm, ball floating far from the fingertips, back foot flat on the rubber, front knee collapsed, left-handed layout, pitcher hopping forward and re-planting the back foot, white or grey pitcher's glove, tape or bandage on the pitching hand, bracelet on the pitching wrist
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
| r_elbow_flex | 32.0 | 20..45 | elbow about 32 deg at release, not fully straight | OBP-P |
| r_shoulder_elev | 91.0 | 80..105 | shoulder abduction about 91 deg | OBP-P |
| trunk_lean_fwd | 30.0 | 20..50 | trunk forward tilt about 35 deg | OBP-P |
| trunk_lean_right | -19.4 | ..-8 | trunk tilted toward the glove side about 17 deg | OBP-P |
| l_knee_flex | 42.2 | 25..55 | front knee firm or extending (about 40 deg) | OBP-P, CG19 |
| fwd:ball:l_ankle | 42.9 | 0..45 | release about 21 cm in front of the lead ankle | OBP-P |
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
- [ISBS10] Fleisig, ISBS 2010 keynote: stride 83 +/- 4 % of height, lead knee 45 deg, shoulder abduction 93 deg, ER 56 deg, elbow 90 deg at foot contact https://ojs.ub.uni-konstanz.de/cpa/article/view/4377
- [FORT09] Fortenbaugh, Fleisig & Andrews 2009, Sports Health: baseball pitching biomechanics https://doi.org/10.1177/1941738109338546
