# BASEBALL_BAT_LOAD

Right-handed batter loaded at stride-foot contact: side-on to the pitcher, weight back, hands high by the rear shoulder, bat angled up behind the head.

- 이름(ko): 야구 타격 준비, 타격 로드, 스트라이드 착지 타자, 타자 테이크백
- names (en): baseball batting load, hitter stride foot down, batter loaded, swing load

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASEBALL_BAT_LOAD

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 60 deg, turned 44 deg to the athlete's left of the chest line; face pointing down and to the athlete's left. Both eyes on the pitcher's release point.
- Torso: trunk line (hips to shoulders) 26 deg forward of vertical; shoulder line rotated 8 deg to the right of the hip line (hip-shoulder separation).
- Right arm (rear arm, top hand): upper arm raised 113 deg from the side of the trunk, pointing forward and slightly to the athlete's right; elbow fully folded (118 deg flexion); forearm pointing to the athlete's left; palm facing forward and slightly to the athlete's left; wrist extended (cocked back) 29 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.26 m above the floor.
- Left arm (lead arm, bottom hand on the bat): upper arm raised 43 deg from the side of the trunk, pointing down and slightly forward; elbow fully folded (114 deg flexion); forearm pointing up and slightly to the athlete's right and slightly forward; palm facing to the athlete's right and forward; wrist extended (cocked back) 34 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.32 m above the floor.
- Right leg (rear leg): hip flexed 54 deg, abducted 29 deg; knee bent (54 deg flexion); thigh pointing down and slightly to the athlete's right and slightly forward, shin pointing down and slightly backward; ankle dorsiflexed 16 deg; foot flat on the floor.
- Left leg (stride leg (toward the pitcher)): hip flexed 44 deg, abducted 29 deg; knee bent (46 deg flexion); thigh pointing down and slightly to the athlete's left and slightly forward, shin pointing down and slightly backward and slightly to the athlete's left; ankle dorsiflexed 22 deg; foot flat on the floor.
- Base: ankles 90 cm apart (49% of body height, 2.2x shoulder width); every support foot touches the floor, none floats.
- Technique cue: shift weight back and coil the trunk
- Technique cue: stride toward the pitcher while the hands stay back
- Technique cue: right hand on top for a right-handed batter

3. OBJECT_INTERACTION:
- bat (85 cm): gripped at the handle, barrel pointing up and slightly to the athlete's right and slightly forward; sweet spot 1.71 m above the floor.
- Pitcher 18.4 m away toward the direction of play; home plate just in front of the batter's feet.

4. CINEMATIC_CAMERA:
- pitcher_view: eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast center-field view, telephoto compression, catcher and umpire soft behind.
- open_side: eye-level shot, side profile view, 50mm standard lens, full-body shot. From the open side facing the batter's chest, plate in the foreground.
- low_cinema: camera 0.3 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Low wide frame from behind the catcher's area, stadium lights and field behind.

5. KINETIC_ENERGY:
- dust puffing from the landing front foot
- bat still and cocked, tension in the forearms
- helmet reflecting the stadium lights
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed baseball batter loaded and ready to swing as the stride foot lands. Side-on to the pitcher, feet about half the body height apart, both knees bent, weight toward the back leg; trunk bent forward over the plate; both hands together on the handle, right hand on top, held high near the rear shoulder; bat angled up and back behind the head; front shoulder closed, chin on the front shoulder. Shift weight back and coil the trunk. Stride toward the pitcher while the hands stay back. Right hand on top for a right-handed batter. Eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast center-field view, telephoto compression, catcher and umpire soft behind. Dust puffing from the landing front foot; bat still and cocked, tension in the forearms. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, batter facing the pitcher, bat passing through the helmet, hands split apart on the handle, wrong foot striding, both feet in the air
```

## Control images

- `openpose_pitcher_view.png` / `.json`: 1152x896, eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot.
- `openpose_open_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.3 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: head.flex = 60 is beyond the usual range -65..56

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| l_knee_flex | 46.3 | 35..60 | lead knee about 46 deg at stride-foot contact | OBP-H |
| r_knee_flex | 53.5 | 42..68 | rear knee about 55 deg | OBP-H |
| trunk_lean_fwd | 26.0 | 15..40 | trunk flexed about 27 deg | OBP-H |
| hip_shoulder_sep | -8.1 | -25..-5 | shoulders more closed than the hips (about 12-18 deg) | OBP-H |
| r_elbow_flex | 118.0 | 105..140 | rear elbow about 124 deg | OBP-H |
| dist:r_palm:l_palm | 9.1 | ..14 | both hands together on the handle | OBP-H |
| stride_pct_height | 49.3 | 40..60 | ankles about 50 % of height apart | OBP-H |

## Sources

- [OBP-H] Driveline OpenBiomechanics, baseball_hitting (98 hitters, 677 swings): means from the dataset (CC BY-NC-SA 4.0; only summary numbers used here) https://github.com/drivelineresearch/openbiomechanics/tree/main/baseball_hitting
- [WEL95] Welch et al. 1995, JOSPT: hitting kinematics (weight shift, stride, sequence) https://www.jospt.org/doi/10.2519/jospt.1995.22.5.193
- [ESC09] Escamilla et al. 2009, J Appl Biomech: adult vs youth hitting kinematics https://pubmed.ncbi.nlm.nih.gov/19827470/
