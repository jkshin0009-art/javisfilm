# BASEBALL_PITCH_FOOT_CONTACT

Right-handed baseball pitcher at stride-foot contact: long stride landing slightly closed, hips opening while the shoulders stay closed, throwing arm up in the 90/90 position, glove arm pointing at the plate.

- 이름(ko): 야구 투구 착지, 스트라이드 착지, 투수 90/90 자세, 코킹 자세
- names (en): baseball pitch foot contact, stride foot plant, 90/90 arm position, arm cocking

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASEBALL_PITCH_FOOT_CONTACT

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 10 deg, turned 74 deg to the athlete's left of the chest line; face pointing to the athlete's left and slightly forward. Eyes locked on the catcher's mitt.
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
- Pitching from a mound 25 cm high; home plate 18.44 m ahead along the direction of play (the floor here is drawn flat).

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
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, landing on the right foot, forearm hanging down, elbow bent backwards, short shoulder-width stride, glove arm missing, both feet in the air
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

## Sources

- [OBP-P] Driveline OpenBiomechanics, baseball_pitching (100 pitchers, 411 fastballs, 1.85 +/- 0.07 m): means computed from the dataset's point-of-interest and full-signal files (CC BY-NC-SA 4.0; only summary numbers used here) https://github.com/drivelineresearch/openbiomechanics/tree/main/baseball_pitching
- [ISBS10] Fleisig, ISBS 2010 keynote: stride 83 +/- 4 % of height, lead knee 45 deg, shoulder abduction 93 deg, ER 56 deg, elbow 90 deg at foot contact https://ojs.ub.uni-konstanz.de/cpa/article/view/4377
- [CG19] A Clinician's Guide to Analysis of the Pitching Motion (2019): balance point, 90/90 arm position, MER about 170 deg https://pmc.ncbi.nlm.nih.gov/articles/PMC6542879/
- [ASMR22] Biomechanical Analysis of the Throwing Athlete, Arthrosc Sports Med Rehabil 2022: stride over 80 % of height, MER 170-180 deg https://pmc.ncbi.nlm.nih.gov/articles/PMC8811517/
